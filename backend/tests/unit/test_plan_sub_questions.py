"""Unit tests for :class:`PlanSubQuestionsUseCase`.

The use case is exercised entirely through a fake :class:`LLMPort` that records
what it was asked and returns whatever the test wants it to. No adapter, no SDK
and no network is involved — the whole point of injecting a port is that this
is possible, and one test asserts it by making sockets explode.
"""

from __future__ import annotations

import socket
from typing import Any, Mapping, Optional
from uuid import UUID, uuid4

import pytest

from application.use_cases.plan_sub_questions import (
    PLANNING_SCHEMA,
    InvalidPlanningRequest,
    LLMUnavailableError,
    MalformedPlanError,
    PlanSubQuestionsUseCase,
    PlanningError,
)
from domain.entities.sub_question import SubQuestion, SubQuestionStatus
from domain.ports.llm_port import LLMPort
from domain.value_objects.tool_category import ToolCategory

TOPIC = "How does containerization affect backend deployment?"


class _ProviderError(Exception):
    """Stands in for an adapter/SDK failure; the use case must not leak it."""


class _FakeLLM:
    """Recording stand-in for :class:`LLMPort`. It never touches the network."""

    def __init__(
        self, response: Any = None, error: Optional[Exception] = None
    ) -> None:
        self.response = response
        self.error = error
        self.calls: list[tuple[str, Mapping[str, Any]]] = []

    def complete(self, prompt: str) -> str:
        raise AssertionError("the planner must not use complete()")

    def complete_structured(
        self, prompt: str, schema: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        self.calls.append((prompt, schema))
        if self.error is not None:
            raise self.error
        return self.response


def _plan(*texts: str) -> dict[str, Any]:
    """A well-formed planning response containing ``texts``."""
    return {"sub_questions": [{"text": text} for text in texts]}


def _use_case(
    response: Any = None,
    *,
    max_subquestions: int = 5,
    error: Optional[Exception] = None,
) -> tuple[PlanSubQuestionsUseCase, _FakeLLM]:
    llm = _FakeLLM(response=response, error=error)
    return (
        PlanSubQuestionsUseCase(llm=llm, max_subquestions=max_subquestions),
        llm,
    )


# --- port conformance -------------------------------------------------------


def test_fake_satisfies_the_llm_port() -> None:
    # If the fake stops matching LLMPort, these tests stop proving anything.
    assert isinstance(_FakeLLM(), LLMPort)


# --- happy path -------------------------------------------------------------


def test_valid_topic_produces_sub_questions() -> None:
    use_case, _ = _use_case(_plan("What is it?", "What are the tradeoffs?"))

    result = use_case.execute(topic=TOPIC, research_query_id=uuid4())

    assert [type(item) for item in result] == [SubQuestion, SubQuestion]
    assert [item.text for item in result] == ["What is it?", "What are the tradeoffs?"]


def test_every_sub_question_carries_the_research_query_id() -> None:
    research_query_id = uuid4()
    use_case, _ = _use_case(_plan("One?", "Two?", "Three?"))

    result = use_case.execute(topic=TOPIC, research_query_id=research_query_id)

    assert result
    assert all(item.research_query_id == research_query_id for item in result)


def test_every_sub_question_starts_general_and_pending() -> None:
    use_case, _ = _use_case(_plan("One?", "Two?"))

    result = use_case.execute(topic=TOPIC, research_query_id=uuid4())

    # Phase 2 only decomposes; classification is a later phase's job.
    assert all(item.category is ToolCategory.GENERAL for item in result)
    assert all(item.status is SubQuestionStatus.PENDING for item in result)


def test_each_sub_question_gets_its_own_new_uuid() -> None:
    use_case, _ = _use_case(_plan("One?", "Two?", "Three?"))

    result = use_case.execute(topic=TOPIC, research_query_id=uuid4())

    ids = [item.id for item in result]
    assert all(isinstance(id_, UUID) for id_ in ids)
    assert len(set(ids)) == len(ids)


def test_question_text_is_trimmed_and_whitespace_collapsed() -> None:
    use_case, _ = _use_case(_plan("  What   is\n it? "))

    result = use_case.execute(topic=TOPIC, research_query_id=uuid4())

    assert [item.text for item in result] == ["What is it?"]


# --- the prompt the port receives -------------------------------------------


def test_prompt_contains_the_topic_and_the_maximum() -> None:
    use_case, llm = _use_case(_plan("One?"), max_subquestions=4)

    use_case.execute(topic=TOPIC, research_query_id=uuid4())

    assert len(llm.calls) == 1
    prompt, _schema = llm.calls[0]
    assert TOPIC in prompt
    assert "4" in prompt


def test_structured_planning_schema_is_requested() -> None:
    use_case, llm = _use_case(_plan("One?"))

    use_case.execute(topic=TOPIC, research_query_id=uuid4())

    _prompt, schema = llm.calls[0]
    assert schema is PLANNING_SCHEMA
    assert schema["required"] == ["sub_questions"]


# --- caller input -----------------------------------------------------------


@pytest.mark.parametrize("topic", ["", "   ", "\n\t "])
def test_empty_or_whitespace_topic_is_rejected(topic: str) -> None:
    use_case, llm = _use_case(_plan("One?"))

    with pytest.raises(InvalidPlanningRequest):
        use_case.execute(topic=topic, research_query_id=uuid4())

    assert llm.calls == [], "the LLM must not be called for an invalid topic"


def test_non_string_topic_is_rejected() -> None:
    use_case, _ = _use_case(_plan("One?"))

    with pytest.raises(InvalidPlanningRequest):
        use_case.execute(topic=None, research_query_id=uuid4())  # type: ignore[arg-type]


def test_non_uuid_research_query_id_is_rejected() -> None:
    use_case, llm = _use_case(_plan("One?"))

    with pytest.raises(InvalidPlanningRequest):
        use_case.execute(topic=TOPIC, research_query_id="not-a-uuid")  # type: ignore[arg-type]

    assert llm.calls == []


@pytest.mark.parametrize("maximum", [0, -1])
def test_max_subquestions_below_one_is_rejected(maximum: int) -> None:
    with pytest.raises(InvalidPlanningRequest):
        PlanSubQuestionsUseCase(llm=_FakeLLM(), max_subquestions=maximum)


@pytest.mark.parametrize("maximum", ["5", 5.0, None, True])
def test_non_integer_max_subquestions_is_rejected(maximum: Any) -> None:
    with pytest.raises(InvalidPlanningRequest):
        PlanSubQuestionsUseCase(llm=_FakeLLM(), max_subquestions=maximum)


# --- the maximum is enforced ------------------------------------------------


def test_maximum_of_one_returns_at_most_one_question() -> None:
    use_case, _ = _use_case(_plan("One?", "Two?", "Three?"), max_subquestions=1)

    result = use_case.execute(topic=TOPIC, research_query_id=uuid4())

    assert [item.text for item in result] == ["One?"]


def test_exactly_the_maximum_is_returned_in_full() -> None:
    use_case, _ = _use_case(_plan("One?", "Two?", "Three?"), max_subquestions=3)

    result = use_case.execute(topic=TOPIC, research_query_id=uuid4())

    assert [item.text for item in result] == ["One?", "Two?", "Three?"]


def test_more_than_the_maximum_is_truncated_deterministically() -> None:
    use_case, _ = _use_case(
        _plan("One?", "Two?", "Three?", "Four?", "Five?"), max_subquestions=2
    )

    result = use_case.execute(topic=TOPIC, research_query_id=uuid4())

    # Never more than the bound, and the kept ones are the leading ones.
    assert len(result) == 2
    assert [item.text for item in result] == ["One?", "Two?"]


def test_fewer_than_the_maximum_is_left_alone() -> None:
    use_case, _ = _use_case(_plan("One?"), max_subquestions=5)

    assert len(use_case.execute(topic=TOPIC, research_query_id=uuid4())) == 1


# --- duplicates -------------------------------------------------------------


def test_duplicate_questions_are_dropped_keeping_the_first() -> None:
    use_case, _ = _use_case(_plan("One?", "One?", "Two?"))

    result = use_case.execute(topic=TOPIC, research_query_id=uuid4())

    assert [item.text for item in result] == ["One?", "Two?"]


def test_duplicates_differing_only_in_case_or_spacing_are_dropped() -> None:
    use_case, _ = _use_case(_plan("One  question?", "ONE QUESTION?", "Two?"))

    result = use_case.execute(topic=TOPIC, research_query_id=uuid4())

    assert [item.text for item in result] == ["One question?", "Two?"]


def test_deduplication_happens_before_truncation() -> None:
    # Two of the three are the same question, so the cap of 2 must still be
    # filled with two *distinct* questions.
    use_case, _ = _use_case(_plan("One?", "one?", "Two?"), max_subquestions=2)

    result = use_case.execute(topic=TOPIC, research_query_id=uuid4())

    assert [item.text for item in result] == ["One?", "Two?"]


# --- malformed model output -------------------------------------------------


@pytest.mark.parametrize("text", ["", "   ", "\n"])
def test_empty_question_text_is_rejected(text: str) -> None:
    use_case, _ = _use_case(_plan("One?", text))

    with pytest.raises(MalformedPlanError):
        use_case.execute(topic=TOPIC, research_query_id=uuid4())


def test_missing_sub_questions_key_is_a_planning_error() -> None:
    use_case, _ = _use_case({"questions": [{"text": "One?"}]})

    with pytest.raises(MalformedPlanError):
        use_case.execute(topic=TOPIC, research_query_id=uuid4())


@pytest.mark.parametrize(
    "value", ["One?", {"text": "One?"}, 3, None, ("One?",)]
)
def test_wrong_sub_questions_type_is_a_planning_error(value: Any) -> None:
    use_case, _ = _use_case({"sub_questions": value})

    with pytest.raises(MalformedPlanError):
        use_case.execute(topic=TOPIC, research_query_id=uuid4())


@pytest.mark.parametrize(
    "item", ["One?", None, 7, ["One?"], {}, {"question": "One?"}, {"text": 7}]
)
def test_malformed_item_is_a_planning_error(item: Any) -> None:
    use_case, _ = _use_case({"sub_questions": [item]})

    with pytest.raises(MalformedPlanError):
        use_case.execute(topic=TOPIC, research_query_id=uuid4())


@pytest.mark.parametrize("response", [None, "sub_questions", ["One?"], 42])
def test_non_mapping_response_is_a_planning_error(response: Any) -> None:
    use_case, _ = _use_case(response)

    with pytest.raises(MalformedPlanError):
        use_case.execute(topic=TOPIC, research_query_id=uuid4())


def test_empty_plan_is_a_planning_error() -> None:
    # A syntactically valid response that plans nothing is still unusable.
    use_case, _ = _use_case(_plan())

    with pytest.raises(MalformedPlanError):
        use_case.execute(topic=TOPIC, research_query_id=uuid4())


# --- LLM failure ------------------------------------------------------------


def test_llm_failure_becomes_a_planning_error() -> None:
    failure = _ProviderError("upstream exploded")
    use_case, _ = _use_case(error=failure)

    with pytest.raises(LLMUnavailableError) as excinfo:
        use_case.execute(topic=TOPIC, research_query_id=uuid4())

    # The provider's own exception type never escapes, but is kept as the cause.
    assert excinfo.value.__cause__ is failure
    assert "upstream exploded" in str(excinfo.value)


def test_every_failure_mode_is_a_planning_error() -> None:
    # One `except PlanningError` is enough for a caller that does not care why.
    for error in (InvalidPlanningRequest, MalformedPlanError, LLMUnavailableError):
        assert issubclass(error, PlanningError)


# --- no network -------------------------------------------------------------


def test_use_case_makes_no_network_call(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("the use case must not open a network connection")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)

    use_case, _ = _use_case(_plan("One?", "Two?"))

    assert len(use_case.execute(topic=TOPIC, research_query_id=uuid4())) == 2

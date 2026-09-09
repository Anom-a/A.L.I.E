"""PlanSubQuestionsUseCase — decompose a research topic into sub-questions.

The first use case of the application layer. It turns one research topic into a
bounded list of domain :class:`SubQuestion` objects by asking an injected
:class:`~domain.ports.llm_port.LLMPort` for a structured plan.

The use case does **no I/O of its own**: it holds a port, not a client, so it
never learns which provider answers, never opens a socket, and never reads
configuration — ``max_subquestions`` is injected for that same reason.

Its scope is deliberately narrow: *decomposition only*. Routing (choosing a
:class:`ToolCategory` and a gateway), retrieval, criticism and synthesis all
belong to later phases, so every planned sub-question is created as
``ToolCategory.GENERAL`` and a later phase reclassifies it.

Model output is never trusted: the structured response is validated key by key,
duplicates are dropped, and the result is truncated to the configured maximum
before any domain entity is built.
"""

from __future__ import annotations

from typing import Any, Mapping
from uuid import UUID

from domain.entities.sub_question import SubQuestion
from domain.ports.llm_port import LLMPort
from domain.value_objects.tool_category import ToolCategory

_SUB_QUESTIONS_KEY = "sub_questions"
_TEXT_KEY = "text"

#: Framework-agnostic description of the planning response, handed to the port.
#: Only decomposition is requested — no category, no tool, no ranking.
PLANNING_SCHEMA: Mapping[str, Any] = {
    "title": "sub_question_plan",
    "type": "object",
    "additionalProperties": False,
    "properties": {
        _SUB_QUESTIONS_KEY: {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {_TEXT_KEY: {"type": "string"}},
                "required": [_TEXT_KEY],
            },
        }
    },
    "required": [_SUB_QUESTIONS_KEY],
}

# Kept here, in the application layer: the domain must not contain prompts.
_PROMPT_TEMPLATE = """You are a research planner. Break the research topic below \
into at most {max_subquestions} independent research questions.

Research topic: {topic}

Requirements:
- Together the questions must cover the major aspects needed to answer the topic.
- Each question must be researchable on its own, without needing the answer to \
another question first.
- Do not repeat or merely rephrase another question.
- Return at most {max_subquestions} questions; fewer if the topic needs fewer.
- Return ONLY a JSON object shaped like \
{{"{key}": [{{"{text}": "..."}}]}} — no prose, no extra keys.
"""


class PlanningError(Exception):
    """Base class for every failure of the planning use case.

    Callers that do not care *why* planning failed can catch this one type; the
    three subclasses below separate the cases that call for different handling.
    """


class InvalidPlanningRequest(PlanningError):
    """The caller supplied invalid input (bad topic, id, or bound)."""


class MalformedPlanError(PlanningError):
    """The model answered, but its structured output was unusable."""


class LLMUnavailableError(PlanningError):
    """The LLM call itself failed, so nothing was planned."""


class PlanSubQuestionsUseCase:
    """Decompose one research topic into domain :class:`SubQuestion` objects."""

    def __init__(self, llm: LLMPort, max_subquestions: int) -> None:
        """Wire the use case to a port and a bound.

        Args:
            llm: Any :class:`LLMPort` implementation. The concrete adapter is
                injected from outside; this class never constructs one.
            max_subquestions: Upper bound on the number of sub-questions
                returned. Comes from configuration, which the use case itself
                knows nothing about.
        """
        if isinstance(max_subquestions, bool) or not isinstance(max_subquestions, int):
            raise InvalidPlanningRequest(
                f"max_subquestions must be an int, got {type(max_subquestions).__name__}"
            )
        if max_subquestions < 1:
            raise InvalidPlanningRequest(
                f"max_subquestions must be at least 1, got {max_subquestions}"
            )
        self._llm = llm
        self._max_subquestions = max_subquestions

    def execute(self, topic: str, research_query_id: UUID) -> list[SubQuestion]:
        """Plan ``topic`` into at most ``max_subquestions`` sub-questions.

        Args:
            topic: The research request to decompose.
            research_query_id: Identifier of the owning research query; every
                returned sub-question is attached to it.

        Returns:
            Pending, ``GENERAL``-category sub-questions in the model's order,
            deduplicated and never longer than the configured maximum.

        Raises:
            InvalidPlanningRequest: ``topic`` or ``research_query_id`` is invalid.
            LLMUnavailableError: the LLM call failed.
            MalformedPlanError: the response did not match the planning schema.
        """
        clean_topic = _require_topic(topic)
        if not isinstance(research_query_id, UUID):
            raise InvalidPlanningRequest(
                f"research_query_id must be a UUID, got {type(research_query_id).__name__}"
            )

        prompt = _planning_prompt(clean_topic, self._max_subquestions)
        try:
            response = self._llm.complete_structured(prompt, PLANNING_SCHEMA)
        except Exception as exc:  # noqa: BLE001 - deliberate port boundary
            # Broad on purpose: the port makes no promise about which exception
            # type an adapter raises, and no adapter error may escape as-is.
            raise LLMUnavailableError(
                f"planning LLM call failed: {type(exc).__name__}: {exc}"
            ) from exc

        # Truncation is the last step, so the cap applies to *usable* questions.
        texts = _planned_texts(response)[: self._max_subquestions]
        return [
            SubQuestion(
                research_query_id=research_query_id,
                text=text,
                # Phase 2 only decomposes. A later phase classifies and routes.
                category=ToolCategory.GENERAL,
            )
            # id (a fresh UUID) and status (PENDING) come from the entity's own
            # defaults rather than being re-decided here.
            for text in texts
        ]


def _planning_prompt(topic: str, max_subquestions: int) -> str:
    """Render the planning instruction for ``topic``."""
    return _PROMPT_TEMPLATE.format(
        topic=topic,
        max_subquestions=max_subquestions,
        key=_SUB_QUESTIONS_KEY,
        text=_TEXT_KEY,
    )


def _require_topic(topic: str) -> str:
    """Return the normalised ``topic``, rejecting anything unusable."""
    if not isinstance(topic, str) or not topic.strip():
        raise InvalidPlanningRequest("topic must be a non-empty string")
    return _normalise(topic)


def _planned_texts(response: Any) -> list[str]:
    """Validate a structured planning response into ordered, unique texts.

    Duplicates (ignoring case and whitespace) are dropped, keeping the first
    occurrence so the result is deterministic. Anything the schema did not ask
    for — a missing key, a wrong type, an item without usable text — is a
    :class:`MalformedPlanError` rather than something silently accepted.
    """
    if not isinstance(response, Mapping):
        raise MalformedPlanError(
            f"planning response must be a mapping, got {type(response).__name__}"
        )
    if _SUB_QUESTIONS_KEY not in response:
        raise MalformedPlanError(f"planning response has no {_SUB_QUESTIONS_KEY!r} key")

    items = response[_SUB_QUESTIONS_KEY]
    if not isinstance(items, list):
        raise MalformedPlanError(
            f"{_SUB_QUESTIONS_KEY!r} must be a list, got {type(items).__name__}"
        )

    texts: list[str] = []
    seen: set[str] = set()
    for position, item in enumerate(items):
        text = _item_text(item, position)
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        texts.append(text)

    if not texts:
        raise MalformedPlanError("planning response contained no sub-questions")
    return texts


def _item_text(item: Any, position: int) -> str:
    """Return the normalised question text of one planned item."""
    if not isinstance(item, Mapping):
        raise MalformedPlanError(
            f"sub-question {position} must be an object, got {type(item).__name__}"
        )
    text = item.get(_TEXT_KEY)
    if not isinstance(text, str) or not text.strip():
        raise MalformedPlanError(
            f"sub-question {position} has no non-empty {_TEXT_KEY!r}"
        )
    return _normalise(text)


def _normalise(value: str) -> str:
    """Trim and collapse whitespace so comparisons and output stay tidy."""
    return " ".join(value.split())

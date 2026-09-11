"""Unit tests for CritiqueEvidenceUseCase."""

from __future__ import annotations

from typing import Any, Mapping
from uuid import uuid4

import pytest

from application.use_cases.critique_evidence import (
    CRITIQUE_SCHEMA,
    CritiqueError,
    CritiqueEvidenceUseCase,
    CritiqueResult,
)
from domain.entities.citation import Citation
from domain.entities.evidence import Evidence, SourceType
from domain.entities.sub_question import SubQuestion
from domain.ports.llm_port import LLMPort
from domain.value_objects.tool_category import ToolCategory


class _FakeLLMPort(LLMPort):
    """A fake LLM that returns a pre-configured structured response."""

    def __init__(self, response: Mapping[str, Any] | Exception) -> None:
        self._response = response
        self.last_prompt = ""

    def complete(self, prompt: str) -> str:
        raise NotImplementedError

    def complete_structured(
        self, prompt: str, schema: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        self.last_prompt = prompt
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


def _sq() -> SubQuestion:
    return SubQuestion(
        research_query_id=uuid4(),
        text="What is the capital of France?",
        category=ToolCategory.GENERAL,
    )


from datetime import datetime, timezone

def _ev() -> list[Evidence]:
    return [
        Evidence(
            sub_question_id=uuid4(),
            content="The capital of France is Paris.",
            source_type=SourceType.WEB,
            citation=Citation(
                source_name="Example",
                source_url_or_id="http://example.com",
                retrieved_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
            ),
        )
    ]


def test_satisfied_verdict() -> None:
    fake_llm = _FakeLLMPort(
        {
            "satisfied": True,
            "reason": "It says Paris.",
            "missing_aspects": [],
        }
    )
    uc = CritiqueEvidenceUseCase(llm=fake_llm)
    result = uc.execute(_sq(), _ev())

    assert result.satisfied is True
    assert result.reason == "It says Paris."
    assert result.missing_aspects == []


def test_unsatisfied_verdict() -> None:
    fake_llm = _FakeLLMPort(
        {
            "satisfied": False,
            "reason": "Does not mention the capital.",
            "missing_aspects": ["The capital name"],
        }
    )
    uc = CritiqueEvidenceUseCase(llm=fake_llm)
    result = uc.execute(_sq(), _ev())

    assert result.satisfied is False
    assert result.reason == "Does not mention the capital."
    assert result.missing_aspects == ["The capital name"]


def test_empty_evidence_produces_deterministic_unsatisfied_result() -> None:
    fake_llm = _FakeLLMPort(Exception("Should not be called!"))
    uc = CritiqueEvidenceUseCase(llm=fake_llm)
    
    result = uc.execute(_sq(), [])
    
    assert result.satisfied is False
    assert result.reason == "No evidence was retrieved."
    assert len(result.missing_aspects) == 1
    assert "lack of evidence" in result.missing_aspects[0]


def test_llm_failure_becomes_critique_error() -> None:
    fake_llm = _FakeLLMPort(ValueError("Network error"))
    uc = CritiqueEvidenceUseCase(llm=fake_llm)
    
    with pytest.raises(CritiqueError, match="critic LLM call failed: ValueError"):
        uc.execute(_sq(), _ev())


def test_prompt_contains_question_and_evidence() -> None:
    fake_llm = _FakeLLMPort(
        {"satisfied": True, "reason": "ok", "missing_aspects": []}
    )
    uc = CritiqueEvidenceUseCase(llm=fake_llm)
    sq = _sq()
    ev = _ev()
    uc.execute(sq, ev)

    assert sq.text in fake_llm.last_prompt
    assert ev[0].content in fake_llm.last_prompt
    assert ev[0].citation.source_name in fake_llm.last_prompt


@pytest.mark.parametrize(
    "bad_response, match",
    [
        (None, "must be a mapping"),
        ([], "must be a mapping"),
        ({"reason": "ok", "missing_aspects": []}, "missing key: satisfied"),
        ({"satisfied": "yes", "reason": "ok", "missing_aspects": []}, "satisfied must be a bool"),
        ({"satisfied": True, "missing_aspects": []}, "missing key: reason"),
        ({"satisfied": True, "reason": "", "missing_aspects": []}, "reason must be a non-empty string"),
        ({"satisfied": True, "reason": "ok"}, "missing key: missing_aspects"),
        ({"satisfied": True, "reason": "ok", "missing_aspects": "none"}, "missing_aspects must be a list"),
        ({"satisfied": True, "reason": "ok", "missing_aspects": [""]}, "must be a non-empty string"),
        ({"satisfied": True, "reason": "ok", "missing_aspects": [123]}, "must be a non-empty string"),
    ],
)
def test_malformed_response_rejected(bad_response: Any, match: str) -> None:
    fake_llm = _FakeLLMPort(bad_response)
    uc = CritiqueEvidenceUseCase(llm=fake_llm)
    
    with pytest.raises(CritiqueError, match=match):
        uc.execute(_sq(), _ev())

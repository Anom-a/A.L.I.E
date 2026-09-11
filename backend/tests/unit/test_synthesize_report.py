"""Unit tests for SynthesizeReportUseCase."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

import pytest

from application.use_cases.synthesize_report import (
    SYNTHESIS_SCHEMA,
    SynthesizeReportUseCase,
    SynthesisError,
)
from domain.entities.citation import Citation
from domain.entities.evidence import Evidence, SourceType
from domain.entities.research_query import ResearchQuery
from domain.entities.sub_question import SubQuestion
from domain.ports.llm_port import LLMPort
from domain.value_objects.tool_category import ToolCategory

FIXED_NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)

class _FakeLLMPort(LLMPort):
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


def _rq() -> ResearchQuery:
    return ResearchQuery(topic="What are the benefits of Rust?")

def _sq1(rq_id) -> SubQuestion:
    return SubQuestion(research_query_id=rq_id, text="Is it memory safe?", category=ToolCategory.GENERAL)

def _sq2(rq_id) -> SubQuestion:
    return SubQuestion(research_query_id=rq_id, text="Is it fast?", category=ToolCategory.GENERAL)

def _ev1(sq_id) -> Evidence:
    return Evidence(
        sub_question_id=sq_id,
        content="Rust guarantees memory safety without a garbage collector.",
        source_type=SourceType.WEB,
        citation=Citation(
            source_name="Rust Lang",
            source_url_or_id="https://rust-lang.org",
            retrieved_at=FIXED_NOW,
        ),
    )

def _ev2(sq_id) -> Evidence:
    return Evidence(
        sub_question_id=sq_id,
        content="Rust is blazingly fast.",
        source_type=SourceType.DOCUMENTATION,
        citation=Citation(
            source_name="Rust Book",
            source_url_or_id="https://doc.rust-lang.org/book",
            retrieved_at=FIXED_NOW,
        ),
    )


def test_valid_evidence_produces_report() -> None:
    fake_llm = _FakeLLMPort(
        {
            "title": "Rust Benefits",
            "sections": [
                {
                    "title": "Memory Safety",
                    "content": "It is safe.",
                    "citation_ids": ["CIT-001"],
                }
            ],
        }
    )
    uc = SynthesizeReportUseCase(llm=fake_llm, clock=lambda: FIXED_NOW)
    rq = _rq()
    sq = _sq1(rq.id)
    ev = _ev1(sq.id)
    
    report = uc.execute(rq, [sq], [ev])
    
    # query ID is preserved
    assert report.query_id == rq.id
    # generated report contains sections
    assert len(report.sections) == 1
    assert report.sections[0].title == "Memory Safety"
    # valid citation IDs are preserved (mapped back to domain ID)
    assert report.sections[0].citation_ids == ("https://rust-lang.org",)
    # Report citations originate from supplied Evidence
    assert len(report.citations) == 1
    assert report.citations[0] == ev.citation


def test_zero_evidence_raises_synthesis_error() -> None:
    fake_llm = _FakeLLMPort({"title": "Test", "sections": []})
    uc = SynthesizeReportUseCase(llm=fake_llm)
    rq = _rq()
    
    with pytest.raises(SynthesisError, match="because no evidence was retrieved"):
        uc.execute(rq, [], [])
    
    # zero evidence does not call the LLM
    assert not fake_llm.last_prompt


def test_unknown_citation_id_raises_synthesis_error() -> None:
    fake_llm = _FakeLLMPort(
        {
            "title": "Rust Benefits",
            "sections": [
                {
                    "title": "Findings",
                    "content": "Some finding.",
                    "citation_ids": ["CIT-999"],
                }
            ],
        }
    )
    uc = SynthesizeReportUseCase(llm=fake_llm)
    rq = _rq()
    sq = _sq1(rq.id)
    ev = _ev1(sq.id)
    
    with pytest.raises(SynthesisError, match="Unknown citation ID generated: CIT-999"):
        uc.execute(rq, [sq], [ev])


def test_duplicate_citation_identifiers_in_input_are_handled() -> None:
    fake_llm = _FakeLLMPort(
        {
            "title": "Rust Benefits",
            "sections": [
                {
                    "title": "Findings",
                    "content": "Some finding.",
                    "citation_ids": ["CIT-001"],
                }
            ],
        }
    )
    uc = SynthesizeReportUseCase(llm=fake_llm, clock=lambda: FIXED_NOW)
    rq = _rq()
    sq = _sq1(rq.id)
    ev = _ev1(sq.id)
    # create another evidence with the exact same citation object
    ev_duplicate = Evidence(
        sub_question_id=sq.id,
        content="Another excerpt from the same source.",
        source_type=ev.source_type,
        citation=ev.citation
    )
    
    # Should not raise exception
    report = uc.execute(rq, [sq], [ev, ev_duplicate])
    assert len(report.citations) == 1
    assert report.citations[0] == ev.citation


@pytest.mark.parametrize(
    "bad_response, match",
    [
        (None, "must be a mapping"),
        ([], "must be a mapping"),
        ({"sections": []}, "missing key: title"),
        ({"title": 123, "sections": []}, "title must be a non-empty string"),
        ({"title": "", "sections": []}, "title must be a non-empty string"),
        ({"title": "ok"}, "missing key: sections"),
        ({"title": "ok", "sections": "none"}, "sections must be a list"),
        (
            {"title": "ok", "sections": ["not a dict"]},
            "must be a mapping",
        ),
        (
            {"title": "ok", "sections": [{"content": "a", "citation_ids": []}]},
            "title must be a non-empty string",
        ),
        (
            {"title": "ok", "sections": [{"title": "", "content": "a", "citation_ids": []}]},
            "title must be a non-empty string",
        ),
        (
            {"title": "ok", "sections": [{"title": "ok", "citation_ids": []}]},
            "content must be a non-empty string",
        ),
        (
            {"title": "ok", "sections": [{"title": "ok", "content": "", "citation_ids": []}]},
            "content must be a non-empty string",
        ),
        (
            {"title": "ok", "sections": [{"title": "ok", "content": "a"}]},
            "citation_ids must be a list",
        ),
        (
            {"title": "ok", "sections": [{"title": "ok", "content": "a", "citation_ids": "none"}]},
            "citation_ids must be a list",
        ),
        (
            {"title": "ok", "sections": [{"title": "ok", "content": "a", "citation_ids": [123]}]},
            "must be a string",
        ),
    ],
)
def test_malformed_llm_output_is_rejected(bad_response: Any, match: str) -> None:
    fake_llm = _FakeLLMPort(bad_response)
    uc = SynthesizeReportUseCase(llm=fake_llm)
    rq = _rq()
    sq = _sq1(rq.id)
    ev = _ev1(sq.id)
    
    with pytest.raises(SynthesisError, match=match):
        uc.execute(rq, [sq], [ev])


def test_llm_failure_produces_synthesis_error() -> None:
    fake_llm = _FakeLLMPort(ValueError("API down"))
    uc = SynthesizeReportUseCase(llm=fake_llm)
    rq = _rq()
    sq = _sq1(rq.id)
    ev = _ev1(sq.id)
    
    with pytest.raises(SynthesisError, match="LLM synthesis failed: ValueError: API down"):
        uc.execute(rq, [sq], [ev])


def test_unresolved_research_gaps_are_communicated_to_llm() -> None:
    fake_llm = _FakeLLMPort(
        {
            "title": "Rust",
            "sections": [
                {
                    "title": "Safety",
                    "content": "Safe.",
                    "citation_ids": ["CIT-001"],
                }
            ],
        }
    )
    uc = SynthesizeReportUseCase(llm=fake_llm)
    rq = _rq()
    sq_safe = _sq1(rq.id)
    sq_fast = _sq2(rq.id)  # This one will have no evidence
    ev = _ev1(sq_safe.id)
    
    uc.execute(rq, [sq_safe, sq_fast], [ev])
    
    prompt = fake_llm.last_prompt
    assert "Unresolved Gaps (No evidence retrieved):" in prompt
    assert sq_fast.text in prompt


def test_unused_evidence_does_not_cause_failure() -> None:
    fake_llm = _FakeLLMPort(
        {
            "title": "Rust",
            "sections": [
                {
                    "title": "Safety",
                    "content": "Safe.",
                    "citation_ids": ["CIT-001"],
                }
            ],
        }
    )
    uc = SynthesizeReportUseCase(llm=fake_llm, clock=lambda: FIXED_NOW)
    rq = _rq()
    sq = _sq1(rq.id)
    ev1 = _ev1(sq.id)
    ev2 = _ev2(sq.id)
    
    # LLM only cites CIT-001 (ev1)
    report = uc.execute(rq, [sq], [ev1, ev2])
    
    assert len(report.citations) == 1
    assert report.citations[0] == ev1.citation

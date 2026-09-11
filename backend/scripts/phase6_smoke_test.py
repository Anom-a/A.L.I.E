#!/usr/bin/env python3
"""Phase 6 smoke test: Synthesizer + Report integration.

Demonstrates the report synthesis flow.
Uses a fake LLM port to strictly demonstrate the decision paths
without network I/O.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from application.use_cases.synthesize_report import SynthesizeReportUseCase, SynthesisError
from domain.entities.citation import Citation
from domain.entities.evidence import Evidence, SourceType
from domain.entities.research_query import ResearchQuery
from domain.entities.sub_question import SubQuestion
from domain.ports.llm_port import LLMPort
from domain.value_objects.tool_category import ToolCategory


class FakeLLM(LLMPort):
    def __init__(self, response: Mapping[str, Any]) -> None:
        self._response = response

    def complete(self, prompt: str) -> str:
        raise NotImplementedError

    def complete_structured(
        self, prompt: str, schema: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        return self._response


def main() -> int:
    print("Phase 6 Synthesizer\n")
    
    rq = ResearchQuery(topic="Is Rust memory safe?")
    sq = SubQuestion(
        research_query_id=rq.id,
        text="Does it have a garbage collector?",
        category=ToolCategory.GENERAL
    )
    ev = Evidence(
        sub_question_id=sq.id,
        content="Rust does not have a garbage collector. It uses ownership and borrowing.",
        source_type=SourceType.DOCUMENTATION,
        citation=Citation(
            source_name="Rust Lang",
            source_url_or_id="https://rust-lang.org",
            retrieved_at=datetime.now(timezone.utc),
        )
    )

    # ---------------------------------------------------------
    # Case 1: Valid Synthesis
    # ---------------------------------------------------------
    print("Case 1: Valid synthesis")
    fake_llm_valid = FakeLLM(
        {
            "title": "Rust Memory Safety",
            "sections": [
                {
                    "title": "Garbage Collection",
                    "content": "Rust has no garbage collector.",
                    "citation_ids": ["CIT-001"],
                }
            ],
        }
    )
    uc_valid = SynthesizeReportUseCase(llm=fake_llm_valid)
    
    report = uc_valid.execute(rq, [sq], [ev])
    print(f"Report title: {report.sections[0].title}")
    print(f"Sections: {len(report.sections)}")
    print(f"Citations used: {len(report.citations)}")
    print("Citation integrity: PASS\n")


    # ---------------------------------------------------------
    # Case 2: Invalid Citation Synthesis (LLM invents a citation)
    # ---------------------------------------------------------
    print("Case 2: LLM invents a fake citation")
    fake_llm_invalid = FakeLLM(
        {
            "title": "Rust Memory Safety",
            "sections": [
                {
                    "title": "Garbage Collection",
                    "content": "Rust has no garbage collector.",
                    "citation_ids": ["CIT-999"],
                }
            ],
        }
    )
    uc_invalid = SynthesizeReportUseCase(llm=fake_llm_invalid)
    
    try:
        uc_invalid.execute(rq, [sq], [ev])
        print("FAILED: Should have rejected fake citation!")
        return 1
    except SynthesisError as e:
        print(f"Successfully caught error: {e}")
        print("Citation integrity: PASS\n")

    print("Phase 6 smoke test: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

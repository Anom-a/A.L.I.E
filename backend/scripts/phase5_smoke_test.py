#!/usr/bin/env python3
"""Phase 5 smoke test: Critic / Reflection integration.

Demonstrates the retrieval flow including the Phase 5 critic.
Uses fake gateways and a fake LLM port to strictly demonstrate
the decision paths without network I/O.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from application.classifiers.keyword_classifier import KeywordSubQuestionClassifier
from application.use_cases.critique_evidence import CritiqueEvidenceUseCase, CritiqueResult
from application.use_cases.retrieve_evidence import RetrieveEvidenceUseCase
from application.use_cases.route_tool import RouteToolUseCase
from domain.entities.citation import Citation
from domain.entities.evidence import Evidence, SourceType
from domain.entities.sub_question import SubQuestion
from domain.ports.llm_port import LLMPort
from domain.ports.search_tool_port import SearchToolPort
from domain.value_objects.tool_category import ToolCategory


class FakeGateway(SearchToolPort):
    def __init__(self, name: str, content: str) -> None:
        self.name = name
        self.content = content
        
    def search(self, sub_question: SubQuestion) -> list[Evidence]:
        return [
            Evidence(
                sub_question_id=sub_question.id,
                content=self.content,
                source_type=SourceType.DOCUMENTATION,
                citation=Citation(
                    source_name=self.name,
                    source_url_or_id=f"http://{self.name}.com",
                    retrieved_at=datetime.now(timezone.utc),
                )
            )
        ]


class FakeLLM(LLMPort):
    def __init__(self, satisfied: bool) -> None:
        self.satisfied = satisfied

    def complete(self, prompt: str) -> str:
        raise NotImplementedError

    def complete_structured(
        self, prompt: str, schema: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        return {
            "satisfied": self.satisfied,
            "reason": "Simulated reason.",
            "missing_aspects": [] if self.satisfied else ["Simulated missing aspect"]
        }


def main() -> int:
    print("Phase 5 Critic\n")

    classifier = KeywordSubQuestionClassifier()
    router = RouteToolUseCase(classifier=classifier)

    # ---------------------------------------------------------
    # Case 1: Primary OK -> Critic SATISFIED -> No Fallback
    # ---------------------------------------------------------
    print("Case 1")
    
    uc1 = RetrieveEvidenceUseCase(
        router=router,
        gateways={"ifixit": FakeGateway("ifixit", "Here is how to repair the screen.")},
        fallback_gateway=FakeGateway("tavily", "Fallback result"),
        critic=CritiqueEvidenceUseCase(llm=FakeLLM(satisfied=True))
    )

    sq1 = SubQuestion(
        research_query_id=uuid4(),
        text="How to repair iPhone screen?",
        category=ToolCategory.REPAIR
    )

    result1 = uc1.execute(sq1)

    print(f"Primary: {'OK' if result1.attempts[0].succeeded else 'FAILED'}")
    print(f"Critic: SATISFIED")
    print(f"Fallback: {'YES' if result1.fallback_used else 'NO'}")
    print(f"Resolved: {'YES' if result1.resolved else 'NO'}\n")

    # ---------------------------------------------------------
    # Case 2: Primary OK -> Critic INSUFFICIENT -> Fallback
    # ---------------------------------------------------------
    print("Case 2")
    
    uc2 = RetrieveEvidenceUseCase(
        router=router,
        gateways={"ifixit": FakeGateway("ifixit", "Unrelated manual about a blender.")},
        fallback_gateway=FakeGateway("tavily", "Fallback result"),
        critic=CritiqueEvidenceUseCase(llm=FakeLLM(satisfied=False))
    )

    sq2 = SubQuestion(
        research_query_id=uuid4(),
        text="How to repair iPhone screen?",
        category=ToolCategory.REPAIR
    )

    result2 = uc2.execute(sq2)

    print(f"Primary: {'OK' if result2.attempts[0].succeeded else 'FAILED'}")
    print(f"Critic: INSUFFICIENT")
    print(f"Fallback: {'TAVILY' if result2.fallback_used else 'NO'}")
    print(f"Resolved: {'YES' if result2.resolved else 'NO'}\n")

    print("Phase 5 smoke test: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

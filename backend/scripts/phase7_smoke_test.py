#!/usr/bin/env python3
"""Smoke test for Phase 7 LangGraph wiring.

Runs the ResearchGraph end-to-end using Fake components to prove
that the full control flow works without making HTTP calls.
"""

import sys
from uuid import uuid4
from datetime import datetime, timezone

from application.graph.research_graph import ResearchGraph
from application.use_cases.plan_sub_questions import PlanSubQuestionsUseCase
from application.use_cases.route_tool import RouteToolUseCase
from application.classifiers.keyword_classifier import KeywordSubQuestionClassifier
from application.use_cases.critique_evidence import CritiqueEvidenceUseCase
from application.use_cases.synthesize_report import SynthesizeReportUseCase
from domain.entities.research_query import ResearchQuery
from domain.entities.evidence import Evidence, SourceType
from domain.entities.citation import Citation

# Import fakes from tests to avoid duplicating code
sys.path.append(".")
from tests.unit.test_research_graph import FakeLLM, FakeSearch

def main():
    print("Setting up Phase 7 Smoke Test...")
    llm = FakeLLM(
        plan_resp={"sub_questions": [{"text": "What is the battery capacity?"}, {"text": "How to open the case?"}]},
        critique_resps=[
            {"satisfied": True, "reason": "Good", "missing_aspects": []},
            {"satisfied": False, "reason": "Bad", "missing_aspects": ["tools"]},
            {"satisfied": True, "reason": "Good now", "missing_aspects": []} # Fallback for Q2
        ],
        synth_resp={
            "title": "Smoke Test Report",
            "sections": [
                {"title": "Battery", "content": "The battery capacity is 3000mAh.", "citation_ids": ["CIT-001"]},
                {"title": "Disassembly", "content": "Use a spudger to open the case.", "citation_ids": ["CIT-002"]}
            ],
        },
    )
    
    primary = FakeSearch([
        Evidence(
            sub_question_id=uuid4(), # Will be overwritten by FakeSearch
            source_type=SourceType.DOCUMENTATION,
            content="Primary evidence",
            citation=Citation("https://example.com/1", "Source 1", datetime.now(timezone.utc))
        )
    ])
    fallback = FakeSearch([
        Evidence(
            sub_question_id=uuid4(),
            source_type=SourceType.WEB,
            content="Fallback evidence",
            citation=Citation("https://example.com/2", "Source 2", datetime.now(timezone.utc))
        )
    ])

    planner = PlanSubQuestionsUseCase(llm, max_subquestions=3)
    router = RouteToolUseCase(KeywordSubQuestionClassifier())
    critic = CritiqueEvidenceUseCase(llm)
    synth = SynthesizeReportUseCase(llm)
    
    graph = ResearchGraph(
        planner=planner,
        router=router,
        gateways={"tavily": primary, "ifixit": primary, "semantic_scholar": primary, "news_api": primary},
        fallback_gateway=fallback,
        critic=critic,
        synthesizer=synth,
        max_loops=2,
    )

    query = ResearchQuery(topic="iPhone 15 repair guide")
    
    print("\nInvoking ResearchGraph...")
    report = graph.invoke(query)
    
    print("\n=== Graph Execution Complete ===")
    print(f"Report for Query ID: {report.query_id}")
    print(f"Total Sections: {len(report.sections)}")
    for section in report.sections:
        print(f"\n# {section.title}\n{section.content}\nCitations: {section.citation_ids}")
        
    print("\n=== Call Statistics ===")
    print(f"LLM Calls: {llm.calls} (Expected: 1 plan + 2 primary critiques + 1 synthesis = 4)")
    print(f"Primary Gateway Calls: {primary.calls} (Expected: 2)")
    print(f"Fallback Gateway Calls: {fallback.calls} (Expected: 1)")

    if llm.calls == 4 and primary.calls == 2 and fallback.calls == 1:
        print("\nSUCCESS: Phase 7 smoke test passed.")
        sys.exit(0)
    else:
        print("\nERROR: Call counts do not match expected values.")
        sys.exit(1)

if __name__ == "__main__":
    main()

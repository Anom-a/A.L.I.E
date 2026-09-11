"""Unit tests for Phase 7 LangGraph wiring."""

import os
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4

import pytest

from application.classifiers.keyword_classifier import KeywordSubQuestionClassifier
from application.graph.research_graph import ResearchGraph
from application.use_cases.critique_evidence import CritiqueEvidenceUseCase
from application.use_cases.plan_sub_questions import PlanSubQuestionsUseCase
from application.use_cases.retrieve_evidence import RetrieveEvidenceUseCase
from application.use_cases.route_tool import RouteToolUseCase
from application.use_cases.synthesize_report import SynthesizeReportUseCase
from domain.entities.citation import Citation
from domain.entities.evidence import Evidence, SourceType
from domain.entities.research_query import ResearchQuery
from domain.entities.sub_question import SubQuestion
from domain.ports.llm_port import LLMPort
from domain.ports.search_tool_port import SearchToolPort


# --- Fakes ---

class FakeLLM(LLMPort):
    def __init__(self, plan_resp, critique_resps, synth_resp):
        self.plan_resp = plan_resp
        self.critique_resps = critique_resps  # list of responses to pop from
        self.synth_resp = synth_resp
        self.calls = 0

    def complete(self, prompt: str) -> str:
        return ""

    def complete_structured(
        self, prompt: str, schema: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        self.calls += 1
        if "research planner" in prompt:
            return self.plan_resp
        elif "evidence critic" in prompt:
            if self.critique_resps:
                return self.critique_resps.pop(0)
            return {"satisfied": True, "reason": "default", "missing_aspects": []}
        elif "research synthesizer" in prompt:
            return self.synth_resp
        return {}


class FakeSearch(SearchToolPort):
    def __init__(self, evidence_list=None, error=None):
        self.evidence_list = evidence_list or []
        self.error = error
        self.calls = 0

    def search(self, sub_question: SubQuestion) -> list[Evidence]:
        self.calls += 1
        if self.error:
            raise self.error
        # We must return Evidence with the correct sub_question_id for synthesis
        ev = []
        for e in self.evidence_list:
            ev.append(
                Evidence(
                    sub_question_id=sub_question.id,
                    source_type=e.source_type,
                    content=e.content,
                    citation=e.citation,
                    id=e.id,
                )
            )
        return ev


# --- Helpers ---

def _make_evidence() -> Evidence:
    return Evidence(
        sub_question_id=uuid4(),
        source_type=SourceType.WEB,
        content="fake evidence",
        citation=Citation("https://example.com", "Test", datetime.now(timezone.utc)),
    )


def _setup_graph(llm, primary_gateway, fallback_gateway, max_loops=3):
    planner = PlanSubQuestionsUseCase(llm, max_subquestions=2)
    router = RouteToolUseCase(KeywordSubQuestionClassifier())
    critic = CritiqueEvidenceUseCase(llm)
    synth = SynthesizeReportUseCase(llm)
    
    return ResearchGraph(
        planner=planner,
        router=router,
        gateways={"tavily": primary_gateway, "ifixit": primary_gateway},
        fallback_gateway=fallback_gateway,
        critic=critic,
        synthesizer=synth,
        max_loops=max_loops,
    )


@pytest.fixture
def base_query():
    return ResearchQuery(topic="Test topic")


# --- Tests ---

def test_happy_path(base_query):
    # 1. Happy path: Graph returns report, no fallback calls, no extra loops.
    llm = FakeLLM(
        plan_resp={"sub_questions": [{"text": "Q1"}]},
        critique_resps=[{"satisfied": True, "reason": "ok", "missing_aspects": []}],
        synth_resp={
            "title": "Rep",
            "sections": [
                {"title": "S1", "content": "C1", "citation_ids": ["CIT-001"]}
            ],
        },
    )
    primary = FakeSearch([_make_evidence()])
    fallback = FakeSearch()

    graph = _setup_graph(llm, primary, fallback)
    report = graph.invoke(base_query)

    assert report is not None
    assert report.sections[0].title == "S1"
    assert primary.calls == 1
    assert fallback.calls == 0
    # LLM calls: 1 plan, 1 critique, 1 synthesis = 3
    assert llm.calls == 3


def test_fallback_path(base_query):
    # 2. Fallback path: fake critic rejects primary once, accepts fallback.
    llm = FakeLLM(
        plan_resp={"sub_questions": [{"text": "Q1"}]},
        critique_resps=[
            {"satisfied": False, "reason": "bad", "missing_aspects": ["all"]}, # For primary
            {"satisfied": True, "reason": "good", "missing_aspects": []}       # For fallback
        ],
        synth_resp={
            "title": "Rep",
            "sections": [
                {"title": "S1", "content": "C1", "citation_ids": ["CIT-001"]}
            ],
        },
    )
    primary = FakeSearch([_make_evidence()])
    fallback = FakeSearch([_make_evidence()])

    graph = _setup_graph(llm, primary, fallback)
    report = graph.invoke(base_query)

    assert primary.calls == 1
    assert fallback.calls == 1
    # LLM calls: 1 plan, 1 primary critique, 1 synthesis = 3
    assert llm.calls == 3


def test_unresolved_subquestion(base_query):
    # 3. Unresolved sub-question: both primary and fallback fail.
    llm = FakeLLM(
        plan_resp={"sub_questions": [{"text": "Q1"}, {"text": "Q2"}]},
        # Q1 primary ok, Q2 primary fail, Q2 fallback fail
        critique_resps=[
            {"satisfied": True, "reason": "ok", "missing_aspects": []}, # Q1 ok
            {"satisfied": False, "reason": "bad", "missing_aspects": ["all"]}, # Q2 primary fail
            {"satisfied": False, "reason": "bad", "missing_aspects": ["all"]}, # Q2 fallback fail
        ],
        synth_resp={
            "title": "Rep",
            "sections": [{"title": "S1", "content": "C1", "citation_ids": ["CIT-001"]}],
        },
    )
    primary = FakeSearch([_make_evidence()])
    fallback = FakeSearch([_make_evidence()])

    graph = _setup_graph(llm, primary, fallback, max_loops=0)
    report = graph.invoke(base_query)
    
    assert report is not None
    # Primary called 2 times (for Q1 and Q2)
    assert primary.calls == 2
    # Fallback called 1 time (for Q2)
    assert fallback.calls == 1


def test_loop_bound_pathological_critic(base_query):
    # 4. Loop bound: overall-coverage always reports gaps, never satisfied.
    llm = FakeLLM(
        plan_resp={"sub_questions": [{"text": "Q1"}]},
        critique_resps=[],
        synth_resp={}
    )
    # Patch FakeLLM to always return False for critique
    def patched_complete_structured(prompt, schema):
        llm.calls += 1
        if "research planner" in prompt:
            return {"sub_questions": [{"text": "Q_gap"}]}
        elif "evidence critic" in prompt:
            return {"satisfied": False, "reason": "bad", "missing_aspects": ["all"]}
        elif "research synthesizer" in prompt:
            return {
                "title": "Rep",
                "sections": [{"title": "S1", "content": "C1", "citation_ids": ["CIT-001"]}],
            }
        return {}
    llm.complete_structured = patched_complete_structured
    
    primary = FakeSearch([_make_evidence()])
    fallback = FakeSearch([]) # Must return empty so resolved=False and it loops

    max_loops = 2
    graph = _setup_graph(llm, primary, fallback, max_loops=max_loops)
    try:
        graph.invoke(base_query)
    except Exception as e:
        assert "Cannot synthesize a report because no evidence was retrieved" in str(e)

    # 1 initial plan + 2 gap plans = 3 plans
    # 1 subq per plan -> 3 subqs total
    # Each subq fails primary and fallback -> 3 primary, 3 fallback
    assert primary.calls == 3
    assert fallback.calls == 3


def test_architecture_guard():
    # 5. Architecture guard: no `application/use_cases/*.py` file imports `langgraph`.
    use_cases_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "application",
        "use_cases"
    )
    for filename in os.listdir(use_cases_dir):
        if not filename.endswith(".py") or filename == "__init__.py":
            continue
            
        with open(os.path.join(use_cases_dir, filename)) as f:
            source = f.read()
            
        import_lines = [
            line.strip()
            for line in source.splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        for imp in import_lines:
            assert "langgraph" not in imp.lower(), (
                f"Forbidden import 'langgraph' found in {filename}: {imp}"
            )

"""Phase 7 LangGraph wiring.

This module defines a StateGraph that orchestrates the research use cases.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Mapping, TypedDict
from uuid import UUID

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from application.use_cases.critique_evidence import CritiqueEvidenceUseCase, CritiqueResult
from application.use_cases.plan_sub_questions import PlanSubQuestionsUseCase
from application.use_cases.retrieve_evidence import RetrievalResult, RetrieveEvidenceUseCase
from application.use_cases.route_tool import RouteToolUseCase, RoutedTool
from application.use_cases.synthesize_report import SynthesizeReportUseCase
from domain.entities.evidence import Evidence
from domain.entities.report import Report
from domain.entities.research_query import ResearchQuery
from domain.entities.sub_question import SubQuestion
from domain.entities.tool_call_attempt import ToolCallAttempt
from domain.ports.search_tool_port import SearchToolPort
import logging

logger = logging.getLogger("application")


def _merge_dicts(left: dict | None, right: dict) -> dict:
    if left is None:
        left = {}
    return {**left, **right}


def _add_lists(left: list | None, right: list) -> list:
    if left is None:
        left = []
    return left + right


class ResearchState(TypedDict):
    """The global state for the research graph."""

    research_query: ResearchQuery
    sub_questions: Annotated[list[SubQuestion], _add_lists]
    new_sub_questions: list[SubQuestion]
    evidence: Annotated[dict[UUID, list[Evidence]], _merge_dicts]
    tool_call_attempts: Annotated[list[ToolCallAttempt], _add_lists]
    critique_verdicts: Annotated[dict[UUID, CritiqueResult], _merge_dicts]
    sub_question_resolved: Annotated[dict[UUID, bool], _merge_dicts]
    loops_remaining: int
    report: Report | None
    unresolved_gaps: list[SubQuestion]


class SubQuestionState(TypedDict):
    """The local state for processing a single sub-question."""

    sub_question: SubQuestion
    tool_name: str
    evidence: list[Evidence]
    attempts: list[ToolCallAttempt]
    critique: CritiqueResult | None
    resolved: bool


# Fake implementations to restrict RetrieveEvidenceUseCase to a single step
class _BypassRouter(RouteToolUseCase):
    def __init__(self, fixed_tool: str) -> None:
        self._fixed_tool = fixed_tool

    def execute(self, sub_question: SubQuestion) -> RoutedTool:
        return RoutedTool(
            sub_question_id=sub_question.id,
            category=sub_question.category,
            tool_name=self._fixed_tool
        )

class _BypassCritic(CritiqueEvidenceUseCase):
    def __init__(self) -> None:
        pass

    def execute(self, sub_question: SubQuestion, evidence: list[Evidence]) -> CritiqueResult:
        return CritiqueResult(satisfied=True, reason="bypass", missing_aspects=[])

class _NullGateway(SearchToolPort):
    def search(self, sub_question: SubQuestion) -> list[Evidence]:
        return []


class ResearchGraph:
    """The compiled state graph orchestrator."""

    def __init__(
        self,
        planner: PlanSubQuestionsUseCase,
        router: RouteToolUseCase,
        gateways: dict[str, SearchToolPort],
        fallback_gateway: SearchToolPort,
        critic: CritiqueEvidenceUseCase,
        synthesizer: SynthesizeReportUseCase,
        max_loops: int,
    ) -> None:
        self._planner = planner
        self._router = router
        self._gateways = gateways
        self._fallback_gateway = fallback_gateway
        self._critic = critic
        self._synthesizer = synthesizer
        self._max_loops = max_loops
        self._app = self._build_graph()

    def invoke(self, research_query: ResearchQuery) -> Report:
        """Run the research process to completion."""
        initial_state: dict[str, Any] = {
            "research_query": research_query,
            "sub_questions": [],
            "new_sub_questions": [],
            "evidence": {},
            "tool_call_attempts": [],
            "critique_verdicts": {},
            "sub_question_resolved": {},
            "loops_remaining": self._max_loops,
            "report": None,
            "unresolved_gaps": [],
        }
        final_state = self._app.invoke(initial_state)
        if final_state["report"] is None:
            raise RuntimeError("Graph finished without generating a report")
        return final_state["report"]

    def _build_graph(self) -> Any:
        # Build the subgraph for processing a single sub-question
        sub_builder = StateGraph(SubQuestionState)

        def route_tool_node(state: SubQuestionState) -> dict:
            routed = self._router.execute(state["sub_question"])
            logger.info(
                "Routing decision",
                extra={
                    "job_id": str(state["sub_question"].research_query_id),
                    "sub_question_id": str(state["sub_question"].id),
                    "tool": routed.tool_name,
                },
            )
            return {"tool_name": routed.tool_name}

        def retrieve_evidence_node(state: SubQuestionState) -> dict:
            # Force RetrieveEvidenceUseCase to only do primary retrieval
            bypass_router = _BypassRouter(state["tool_name"])
            bypass_critic = _BypassCritic()
            uc = RetrieveEvidenceUseCase(
                router=bypass_router,
                gateways=self._gateways,
                fallback_gateway=_NullGateway(), # Prevent fallback
                critic=bypass_critic,
            )
            result = uc.execute(state["sub_question"])
            logger.info(
                "Primary retrieval result",
                extra={
                    "job_id": str(state["sub_question"].research_query_id),
                    "sub_question_id": str(state["sub_question"].id),
                    "resolved": result.resolved,
                    "evidence_count": len(result.evidence),
                },
            )
            return {
                "evidence": result.evidence,
                "attempts": result.attempts,
                "resolved": result.resolved
            }

        def critique_evidence_node(state: SubQuestionState) -> dict:
            if not state.get("evidence"):
                critique = CritiqueResult(
                    satisfied=False,
                    reason="No evidence to critique",
                    missing_aspects=["All"]
                )
            else:
                critique = self._critic.execute(state["sub_question"], state["evidence"])
            
            logger.info(
                "Critic verdict",
                extra={
                    "job_id": str(state["sub_question"].research_query_id),
                    "sub_question_id": str(state["sub_question"].id),
                    "satisfied": critique.satisfied,
                },
            )
            return {"critique": critique}

        def retrieve_evidence_fallback_node(state: SubQuestionState) -> dict:
            # Force RetrieveEvidenceUseCase to only do fallback retrieval (by making primary fail)
            bypass_router = _BypassRouter("tavily")
            bypass_critic = _BypassCritic()
            # Primary is tavily, fallback is null.
            uc = RetrieveEvidenceUseCase(
                router=bypass_router,
                gateways={"tavily": self._fallback_gateway},
                fallback_gateway=_NullGateway(),
                critic=bypass_critic,
            )
            
            logger.info(
                "Fallback triggered",
                extra={
                    "job_id": str(state["sub_question"].research_query_id),
                    "sub_question_id": str(state["sub_question"].id),
                },
            )
            
            result = uc.execute(state["sub_question"])
            # Update state with new evidence and attempts, replacing old evidence
            attempts = state.get("attempts", []) + result.attempts
            return {
                "evidence": result.evidence,
                "attempts": attempts,
                "resolved": result.resolved
            }

        def route_after_critique(state: SubQuestionState) -> str:
            if state.get("critique") and state["critique"].satisfied:
                return END
            return "retrieve_evidence_fallback_node"

        sub_builder.add_node("route_tool_node", route_tool_node)
        sub_builder.add_node("retrieve_evidence_node", retrieve_evidence_node)
        sub_builder.add_node("critique_evidence_node", critique_evidence_node)
        sub_builder.add_node("retrieve_evidence_fallback_node", retrieve_evidence_fallback_node)

        sub_builder.add_edge(START, "route_tool_node")
        sub_builder.add_edge("route_tool_node", "retrieve_evidence_node")
        sub_builder.add_edge("retrieve_evidence_node", "critique_evidence_node")
        sub_builder.add_conditional_edges("critique_evidence_node", route_after_critique)
        sub_builder.add_edge("retrieve_evidence_fallback_node", END)

        sub_app = sub_builder.compile()

        # Wrapper for Send API mapping
        def process_sub_question_node(state: SubQuestionState) -> dict:
            res = sub_app.invoke(state)
            sq_id = state["sub_question"].id
            return {
                "evidence": {sq_id: res.get("evidence", [])},
                "tool_call_attempts": res.get("attempts", []),
                "critique_verdicts": {sq_id: res["critique"]} if res.get("critique") else {},
                "sub_question_resolved": {sq_id: res.get("resolved", False)}
            }

        # Parent graph
        builder = StateGraph(ResearchState)

        def plan_sub_questions_node(state: ResearchState) -> dict:
            topic = state["research_query"].topic
            if state.get("unresolved_gaps"):
                # Append gaps to topic for additional questions
                gaps_text = "\n".join(f"- {sq.text}" for sq in state["unresolved_gaps"])
                topic = f"{topic}\n\nFocus on these unresolved gaps:\n{gaps_text}"
            
            new_sqs = self._planner.execute(topic, state["research_query"].id)
            
            logger.info(
                "Planning completed",
                extra={
                    "job_id": str(state["research_query"].id),
                    "new_questions_count": len(new_sqs),
                },
            )
            
            return {
                "sub_questions": new_sqs,
                "new_sub_questions": new_sqs,
            }

        def critique_overall_coverage_node(state: ResearchState) -> dict:
            # Determine unresolved gaps from all critiques and evidence
            unresolved = []
            for sq in state["sub_questions"]:
                resolved = state["sub_question_resolved"].get(sq.id, False)
                if not resolved:
                    unresolved.append(sq)
            
            return {"unresolved_gaps": unresolved}

        def synthesize_report_node(state: ResearchState) -> dict:
            # Flatten evidence from dict to list for the usecase
            all_evidence = []
            for ev_list in state["evidence"].values():
                all_evidence.extend(ev_list)
            
            logger.info(
                "Synthesis started",
                extra={"job_id": str(state["research_query"].id)}
            )
            
            report = self._synthesizer.execute(
                research_query=state["research_query"],
                sub_questions=state["sub_questions"],
                evidence=all_evidence,
            )
            return {"report": report}

        def route_after_plan(state: ResearchState) -> list[Send]:
            return [
                Send("process_sub_question_node", {"sub_question": sq})
                for sq in state["new_sub_questions"]
            ]

        def route_after_coverage(state: ResearchState) -> str:
            if not state["unresolved_gaps"] or state["loops_remaining"] <= 0:
                return "synthesize_report_node"
            return "decrement_loop_node"
            
        def decrement_loop_node(state: ResearchState) -> dict:
            return {"loops_remaining": state["loops_remaining"] - 1}

        builder.add_node("plan_sub_questions_node", plan_sub_questions_node)
        builder.add_node("process_sub_question_node", process_sub_question_node)
        builder.add_node("critique_overall_coverage_node", critique_overall_coverage_node)
        builder.add_node("synthesize_report_node", synthesize_report_node)
        builder.add_node("decrement_loop_node", decrement_loop_node)

        builder.add_edge(START, "plan_sub_questions_node")
        builder.add_conditional_edges("plan_sub_questions_node", route_after_plan)
        builder.add_edge("process_sub_question_node", "critique_overall_coverage_node")
        
        builder.add_conditional_edges("critique_overall_coverage_node", route_after_coverage)
        builder.add_edge("decrement_loop_node", "plan_sub_questions_node")
        builder.add_edge("synthesize_report_node", END)

        return builder.compile()


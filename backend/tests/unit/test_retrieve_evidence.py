"""Unit tests for :class:`RetrieveEvidenceUseCase`.

All tests use fake gateways — no network, no LLM, no external API.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest

from application.classifiers.keyword_classifier import KeywordSubQuestionClassifier
from application.use_cases.critique_evidence import CritiqueEvidenceUseCase, CritiqueResult, CritiqueError
from application.use_cases.retrieve_evidence import (
    FALLBACK_TOOL_NAME,
    RetrievalError,
    RetrievalResult,
    RetrieveEvidenceUseCase,
)
from application.use_cases.route_tool import (
    CATEGORY_TO_TOOL,
    RouteToolUseCase,
)
from domain.entities.citation import Citation
from domain.entities.evidence import Evidence, SourceType
from domain.entities.sub_question import SubQuestion
from domain.entities.tool_call_attempt import ToolCallAttempt
from domain.ports.search_tool_port import SearchToolPort
from domain.value_objects.tool_category import ToolCategory

FIXED_NOW = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)
FIXED_LATER = datetime(2026, 9, 11, 12, 1, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fake gateways
# ---------------------------------------------------------------------------

class _FakeGateway:
    """A test double for :class:`SearchToolPort`."""

    def __init__(
        self,
        evidence: list[Evidence] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.evidence = evidence or []
        self.error = error
        self.call_count = 0
        self.calls: list[SubQuestion] = []

    def search(self, sub_question: SubQuestion) -> list[Evidence]:
        self.call_count += 1
        self.calls.append(sub_question)
        if self.error is not None:
            raise self.error
        return self.evidence


class _FakeCritic:
    """A test double for CritiqueEvidenceUseCase."""
    
    def __init__(self, satisfied: bool = True, error: Exception | None = None) -> None:
        self.satisfied = satisfied
        self.error = error
        self.call_count = 0
        self.calls: list[tuple[SubQuestion, list[Evidence]]] = []

    def execute(self, sub_question: SubQuestion, evidence: list[Evidence]) -> CritiqueResult:
        self.call_count += 1
        self.calls.append((sub_question, evidence))
        if self.error is not None:
            raise self.error
        return CritiqueResult(
            satisfied=self.satisfied,
            reason="fake reason",
            missing_aspects=[]
        )


def _make_evidence(sub_question_id=None, content="test content") -> Evidence:
    return Evidence(
        sub_question_id=sub_question_id or uuid4(),
        source_type=SourceType.DOCUMENTATION,
        content=content,
        citation=Citation(
            source_url_or_id="https://example.com/guide",
            source_name="Test Guide",
            retrieved_at=FIXED_NOW,
        ),
    )


def _sq(text: str, category: ToolCategory = ToolCategory.GENERAL) -> SubQuestion:
    return SubQuestion(
        research_query_id=uuid4(),
        text=text,
        category=category,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def classifier() -> KeywordSubQuestionClassifier:
    return KeywordSubQuestionClassifier()


@pytest.fixture()
def router(classifier: KeywordSubQuestionClassifier) -> RouteToolUseCase:
    return RouteToolUseCase(classifier=classifier)


def _build_use_case(
    router: RouteToolUseCase,
    primary_gateway: _FakeGateway,
    fallback_gateway: _FakeGateway,
    primary_tool: str = "ifixit",
    critic: _FakeCritic | None = None,
) -> RetrieveEvidenceUseCase:
    """Wire a use case with a single primary gateway and a fallback."""
    gateways: dict[str, SearchToolPort] = {
        primary_tool: primary_gateway,
    }
    # Also ensure tavily is in the map if the primary isn't tavily,
    # since GENERAL questions route to tavily.
    if primary_tool != "tavily":
        gateways["tavily"] = fallback_gateway
    return RetrieveEvidenceUseCase(
        router=router,
        gateways=gateways,
        fallback_gateway=fallback_gateway,
        critic=critic or _FakeCritic(satisfied=True),  # Default satisfies all
        clock=lambda: FIXED_NOW,
    )


def _build_full_use_case(
    router: RouteToolUseCase,
    gateway_map: dict[str, _FakeGateway],
    fallback: _FakeGateway,
    critic: _FakeCritic | None = None,
) -> RetrieveEvidenceUseCase:
    return RetrieveEvidenceUseCase(
        router=router,
        gateways=gateway_map,  # type: ignore[arg-type]
        fallback_gateway=fallback,
        critic=critic or _FakeCritic(satisfied=True),
        clock=lambda: FIXED_NOW,
    )


# ---------------------------------------------------------------------------
# 1. Primary tool succeeds with evidence
# ---------------------------------------------------------------------------

def test_primary_succeeds_with_evidence(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    ev = _make_evidence(sub_question_id=sq.id)
    primary = _FakeGateway(evidence=[ev])
    fallback = _FakeGateway()

    result = _build_use_case(router, primary, fallback).execute(sq)

    assert primary.call_count == 1
    assert fallback.call_count == 0
    assert result.resolved is True
    assert result.fallback_used is False
    assert len(result.attempts) == 1
    assert result.evidence == [ev]


# ---------------------------------------------------------------------------
# 2. Primary tool returns empty evidence → fallback called
# ---------------------------------------------------------------------------

def test_primary_empty_triggers_fallback(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    fallback_ev = _make_evidence(sub_question_id=sq.id, content="fallback result")
    primary = _FakeGateway(evidence=[])
    fallback = _FakeGateway(evidence=[fallback_ev])

    result = _build_use_case(router, primary, fallback).execute(sq)

    assert primary.call_count == 1
    assert fallback.call_count == 1
    assert result.fallback_used is True


# ---------------------------------------------------------------------------
# 3. Primary tool raises adapter failure → fallback called
# ---------------------------------------------------------------------------

def test_primary_exception_triggers_fallback(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    fallback_ev = _make_evidence(sub_question_id=sq.id, content="fallback result")
    primary = _FakeGateway(error=RuntimeError("API down"))
    fallback = _FakeGateway(evidence=[fallback_ev])

    result = _build_use_case(router, primary, fallback).execute(sq)

    assert primary.call_count == 1
    assert fallback.call_count == 1
    assert result.fallback_used is True


# ---------------------------------------------------------------------------
# 4. Primary fails, fallback succeeds → resolved with fallback evidence
# ---------------------------------------------------------------------------

def test_primary_fails_fallback_succeeds(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    fallback_ev = _make_evidence(sub_question_id=sq.id, content="fallback result")
    primary = _FakeGateway(error=RuntimeError("timeout"))
    fallback = _FakeGateway(evidence=[fallback_ev])

    result = _build_use_case(router, primary, fallback).execute(sq)

    assert result.resolved is True
    assert result.evidence == [fallback_ev]
    assert len(result.attempts) == 2


# ---------------------------------------------------------------------------
# 5. Primary fails, fallback fails → unresolved
# ---------------------------------------------------------------------------

def test_both_fail_unresolved(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    primary = _FakeGateway(error=RuntimeError("primary down"))
    fallback = _FakeGateway(error=RuntimeError("fallback down"))

    result = _build_use_case(router, primary, fallback).execute(sq)

    assert result.resolved is False
    assert result.evidence == []
    assert len(result.attempts) == 2


def test_both_return_empty_unresolved(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    primary = _FakeGateway(evidence=[])
    fallback = _FakeGateway(evidence=[])

    result = _build_use_case(router, primary, fallback).execute(sq)

    assert result.resolved is False
    assert result.evidence == []
    assert result.fallback_used is True


# ---------------------------------------------------------------------------
# 6. Fallback is never called after successful primary
# ---------------------------------------------------------------------------

def test_fallback_never_called_on_primary_success(
    router: RouteToolUseCase,
) -> None:
    sq = _sq("How to repair an iPhone screen?")
    ev = _make_evidence(sub_question_id=sq.id)
    primary = _FakeGateway(evidence=[ev])
    fallback = _FakeGateway(evidence=[_make_evidence()])

    _build_use_case(router, primary, fallback).execute(sq)

    assert fallback.call_count == 0


# ---------------------------------------------------------------------------
# 7. Primary is never called twice
# ---------------------------------------------------------------------------

def test_primary_called_exactly_once(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    primary = _FakeGateway(error=RuntimeError("down"))
    fallback = _FakeGateway(evidence=[_make_evidence(sub_question_id=sq.id)])

    _build_use_case(router, primary, fallback).execute(sq)

    assert primary.call_count == 1


# ---------------------------------------------------------------------------
# 8. Tavily fallback is never called more than once
# ---------------------------------------------------------------------------

def test_fallback_called_at_most_once(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    primary = _FakeGateway(error=RuntimeError("down"))
    fallback = _FakeGateway(error=RuntimeError("also down"))

    _build_use_case(router, primary, fallback).execute(sq)

    assert fallback.call_count == 1


# ---------------------------------------------------------------------------
# 9. Missing configured primary gateway raises clear error
# ---------------------------------------------------------------------------

def test_missing_gateway_raises_retrieval_error(
    router: RouteToolUseCase,
) -> None:
    sq = _sq("How to repair an iPhone screen?")
    # Route will select "ifixit" but it's not in the map.
    fallback = _FakeGateway()
    uc = RetrieveEvidenceUseCase(
        router=router,
        gateways={},  # empty map — no ifixit
        fallback_gateway=fallback,
        critic=_FakeCritic(satisfied=True),
    )

    with pytest.raises(RetrievalError, match="no gateway registered"):
        uc.execute(sq)


# ---------------------------------------------------------------------------
# 10. Every actual call has exactly one ToolCallAttempt
# ---------------------------------------------------------------------------

def test_one_attempt_per_primary_success(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    ev = _make_evidence(sub_question_id=sq.id)
    primary = _FakeGateway(evidence=[ev])
    fallback = _FakeGateway()

    result = _build_use_case(router, primary, fallback).execute(sq)
    assert len(result.attempts) == 1


def test_two_attempts_on_fallback(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    primary = _FakeGateway(error=RuntimeError("down"))
    fallback = _FakeGateway(evidence=[_make_evidence(sub_question_id=sq.id)])

    result = _build_use_case(router, primary, fallback).execute(sq)
    assert len(result.attempts) == 2


# ---------------------------------------------------------------------------
# 11. fallback_used is false for the primary attempt
# ---------------------------------------------------------------------------

def test_primary_attempt_has_fallback_used_false(
    router: RouteToolUseCase,
) -> None:
    sq = _sq("How to repair an iPhone screen?")
    primary = _FakeGateway(error=RuntimeError("down"))
    fallback = _FakeGateway(evidence=[_make_evidence(sub_question_id=sq.id)])

    result = _build_use_case(router, primary, fallback).execute(sq)
    assert result.attempts[0].fallback_used is False


# ---------------------------------------------------------------------------
# 12. fallback_used is true for the fallback attempt
# ---------------------------------------------------------------------------

def test_fallback_attempt_has_fallback_used_true(
    router: RouteToolUseCase,
) -> None:
    sq = _sq("How to repair an iPhone screen?")
    primary = _FakeGateway(error=RuntimeError("down"))
    fallback = _FakeGateway(evidence=[_make_evidence(sub_question_id=sq.id)])

    result = _build_use_case(router, primary, fallback).execute(sq)
    assert result.attempts[1].fallback_used is True


# ---------------------------------------------------------------------------
# 13. Attempt timestamps exist
# ---------------------------------------------------------------------------

def test_attempt_timestamps_exist(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    primary = _FakeGateway(error=RuntimeError("down"))
    fallback = _FakeGateway(evidence=[_make_evidence(sub_question_id=sq.id)])

    result = _build_use_case(router, primary, fallback).execute(sq)
    for attempt in result.attempts:
        assert isinstance(attempt.timestamp, datetime)
        assert attempt.timestamp.tzinfo is not None


# ---------------------------------------------------------------------------
# 14. Returned result preserves the original SubQuestion ID
# ---------------------------------------------------------------------------

def test_result_preserves_sub_question_id(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    ev = _make_evidence(sub_question_id=sq.id)
    primary = _FakeGateway(evidence=[ev])
    fallback = _FakeGateway()

    result = _build_use_case(router, primary, fallback).execute(sq)
    assert result.sub_question_id == sq.id


# ---------------------------------------------------------------------------
# 15. The router is actually used to determine the primary tool
# ---------------------------------------------------------------------------

def test_router_determines_primary_tool(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    ev = _make_evidence(sub_question_id=sq.id)
    primary = _FakeGateway(evidence=[ev])
    fallback = _FakeGateway()

    result = _build_use_case(router, primary, fallback).execute(sq)
    assert result.primary_tool == "ifixit"


def test_general_question_routes_to_tavily(router: RouteToolUseCase) -> None:
    sq = _sq("What are the main causes of database deadlocks?")
    ev = _make_evidence(sub_question_id=sq.id)
    tavily = _FakeGateway(evidence=[ev])
    fallback = _FakeGateway()

    uc = RetrieveEvidenceUseCase(
        router=router,
        gateways={"tavily": tavily},
        fallback_gateway=fallback,
        critic=_FakeCritic(),
        clock=lambda: FIXED_NOW,
    )
    result = uc.execute(sq)
    assert result.primary_tool == "tavily"
    assert tavily.call_count == 1


# ---------------------------------------------------------------------------
# Attempt tool names
# ---------------------------------------------------------------------------

def test_primary_attempt_tool_name(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    primary = _FakeGateway(error=RuntimeError("down"))
    fallback = _FakeGateway(evidence=[_make_evidence(sub_question_id=sq.id)])

    result = _build_use_case(router, primary, fallback).execute(sq)
    assert result.attempts[0].tool_name == "ifixit"
    assert result.attempts[1].tool_name == FALLBACK_TOOL_NAME


# ---------------------------------------------------------------------------
# Attempt succeeded flags
# ---------------------------------------------------------------------------

def test_attempt_succeeded_flags(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    primary = _FakeGateway(error=RuntimeError("down"))
    fallback = _FakeGateway(evidence=[_make_evidence(sub_question_id=sq.id)])

    result = _build_use_case(router, primary, fallback).execute(sq)
    assert result.attempts[0].succeeded is False
    assert result.attempts[1].succeeded is True


def test_empty_primary_records_as_failed(router: RouteToolUseCase) -> None:
    """An empty evidence list is treated as failure (not success)."""
    sq = _sq("How to repair an iPhone screen?")
    primary = _FakeGateway(evidence=[])
    fallback = _FakeGateway(evidence=[_make_evidence(sub_question_id=sq.id)])

    result = _build_use_case(router, primary, fallback).execute(sq)
    assert result.attempts[0].succeeded is False


# ---------------------------------------------------------------------------
# Routing failure is wrapped in RetrievalError
# ---------------------------------------------------------------------------

def test_routing_failure_raises_retrieval_error(
    router: RouteToolUseCase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the router raises RoutingError, the use case wraps it."""
    # Force the router's classifier to fail so it raises RoutingError
    def _failing_classifier(*args: Any, **kwargs: Any) -> Any:
        raise ValueError("classifier broken")

    monkeypatch.setattr(router._classifier, "classify", _failing_classifier)

    sq = _sq("How to repair an iPhone screen?", category=ToolCategory.GENERAL)
    fallback = _FakeGateway()
    uc = RetrieveEvidenceUseCase(
        router=router,
        gateways={"tavily": fallback},
        fallback_gateway=fallback,
        critic=_FakeCritic(),
    )
    with pytest.raises(RetrievalError, match="routing failed for sub-question"):
        uc.execute(sq)


def test_invalid_sub_question_routing_error(
    router: RouteToolUseCase,
) -> None:
    """A non-SubQuestion input causes a RetrievalError directly."""
    fallback = _FakeGateway()
    uc = RetrieveEvidenceUseCase(
        router=router,
        gateways={},
        fallback_gateway=fallback,
        critic=_FakeCritic(),
    )
    with pytest.raises(RetrievalError, match="execute\\(\\) expects a SubQuestion"):
        uc.execute("not a SubQuestion")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Default clock is used when none is injected
# ---------------------------------------------------------------------------

def test_default_clock_produces_utc_timestamps(
    router: RouteToolUseCase,
) -> None:
    sq = _sq("How to repair an iPhone screen?")
    ev = _make_evidence(sub_question_id=sq.id)
    primary = _FakeGateway(evidence=[ev])
    fallback = _FakeGateway()

    # Do NOT inject a clock — exercise the default _utc_now path.
    uc = RetrieveEvidenceUseCase(
        router=router,
        gateways={"ifixit": primary, "tavily": fallback},
        fallback_gateway=fallback,
        critic=_FakeCritic(),
    )
    result = uc.execute(sq)
    assert result.attempts[0].timestamp.tzinfo is not None


# ---------------------------------------------------------------------------
# RetrievalResult is frozen
# ---------------------------------------------------------------------------

def test_retrieval_result_is_frozen() -> None:
    result = RetrievalResult(
        sub_question_id=uuid4(),
        evidence=[],
        primary_tool="ifixit",
        fallback_used=False,
        resolved=False,
        attempts=[],
    )
    with pytest.raises(AttributeError):
        result.resolved = True  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Architecture guard — no forbidden imports
# ---------------------------------------------------------------------------

def test_retrieve_evidence_has_no_forbidden_imports() -> None:
    import inspect
    import application.use_cases.retrieve_evidence as mod

    source = inspect.getsource(mod)
    forbidden = [
        "tavily", "openai", "ifixit", "semantic_scholar",
        "news_api", "fastapi", "langgraph", "httpx", "dotenv",
    ]
    import_lines = [
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    for imp in import_lines:
        for name in forbidden:
            assert name not in imp.lower(), (
                f"Forbidden import {name!r} found in retrieve_evidence.py: {imp}"
            )


# ---------------------------------------------------------------------------
# Phase 5: Critic behavior
# ---------------------------------------------------------------------------

def test_primary_succeeds_critic_unsatisfied_fallback_succeeds(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    ev1 = _make_evidence(sub_question_id=sq.id, content="primary evidence")
    ev2 = _make_evidence(sub_question_id=sq.id, content="fallback evidence")
    
    primary = _FakeGateway(evidence=[ev1])
    fallback = _FakeGateway(evidence=[ev2])
    critic = _FakeCritic(satisfied=False)

    result = _build_use_case(router, primary, fallback, critic=critic).execute(sq)

    assert primary.call_count == 1
    assert critic.call_count == 1
    assert fallback.call_count == 1
    assert result.fallback_used is True
    assert result.resolved is True
    assert result.evidence == [ev2]


def test_primary_succeeds_critic_unsatisfied_fallback_fails(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    ev1 = _make_evidence(sub_question_id=sq.id, content="primary evidence")
    
    primary = _FakeGateway(evidence=[ev1])
    fallback = _FakeGateway(error=RuntimeError("fallback down"))
    critic = _FakeCritic(satisfied=False)

    result = _build_use_case(router, primary, fallback, critic=critic).execute(sq)

    assert primary.call_count == 1
    assert critic.call_count == 1
    assert fallback.call_count == 1
    assert result.fallback_used is True
    assert result.resolved is False
    assert result.evidence == []


def test_primary_empty_critic_not_called(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    fallback_ev = _make_evidence(sub_question_id=sq.id)
    
    primary = _FakeGateway(evidence=[])
    fallback = _FakeGateway(evidence=[fallback_ev])
    critic = _FakeCritic(satisfied=True)

    result = _build_use_case(router, primary, fallback, critic=critic).execute(sq)

    assert primary.call_count == 1
    assert critic.call_count == 0
    assert fallback.call_count == 1


def test_primary_fails_critic_not_called(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    fallback_ev = _make_evidence(sub_question_id=sq.id)
    
    primary = _FakeGateway(error=RuntimeError("primary down"))
    fallback = _FakeGateway(evidence=[fallback_ev])
    critic = _FakeCritic(satisfied=True)

    result = _build_use_case(router, primary, fallback, critic=critic).execute(sq)

    assert primary.call_count == 1
    assert critic.call_count == 0
    assert fallback.call_count == 1


def test_critic_failure_raises_critique_error(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair an iPhone screen?")
    ev = _make_evidence(sub_question_id=sq.id)
    
    primary = _FakeGateway(evidence=[ev])
    fallback = _FakeGateway()
    critic = _FakeCritic(error=CritiqueError("LLM offline"))

    with pytest.raises(CritiqueError, match="LLM offline"):
        _build_use_case(router, primary, fallback, critic=critic).execute(sq)

# ---------------------------------------------------------------------------
# Phase 9: Semantic Scholar and News API Fallback
# ---------------------------------------------------------------------------

def test_semantic_scholar_succeeds_critic_satisfied(router: RouteToolUseCase) -> None:
    sq = _sq("A scholarly paper on AI", category=ToolCategory.ACADEMIC)
    ev = _make_evidence(sub_question_id=sq.id)
    primary = _FakeGateway(evidence=[ev])
    fallback = _FakeGateway()
    critic = _FakeCritic(satisfied=True)
    
    result = _build_use_case(router, primary, fallback, primary_tool="semantic_scholar", critic=critic).execute(sq)
    
    assert primary.call_count == 1
    assert critic.call_count == 1
    assert fallback.call_count == 0
    assert result.fallback_used is False
    assert result.resolved is True

def test_semantic_scholar_fails_fallback_succeeds(router: RouteToolUseCase) -> None:
    sq = _sq("A scholarly paper on AI", category=ToolCategory.ACADEMIC)
    fallback_ev = _make_evidence(sub_question_id=sq.id, content="fallback")
    primary = _FakeGateway(error=RuntimeError("timeout"))
    fallback = _FakeGateway(evidence=[fallback_ev])
    
    result = _build_use_case(router, primary, fallback, primary_tool="semantic_scholar").execute(sq)
    
    assert primary.call_count == 1
    assert fallback.call_count == 1
    assert result.fallback_used is True
    assert result.resolved is True
    assert result.attempts[1].fallback_used is True
    assert result.evidence == [fallback_ev]

def test_semantic_scholar_and_fallback_fail(router: RouteToolUseCase) -> None:
    sq = _sq("A scholarly paper on AI", category=ToolCategory.ACADEMIC)
    primary = _FakeGateway(error=RuntimeError("primary down"))
    fallback = _FakeGateway(error=RuntimeError("fallback down"))
    
    result = _build_use_case(router, primary, fallback, primary_tool="semantic_scholar").execute(sq)
    
    assert result.resolved is False
    assert result.evidence == []
    assert len(result.attempts) == 2

def test_news_api_succeeds_critic_satisfied(router: RouteToolUseCase) -> None:
    sq = _sq("Latest news on AI", category=ToolCategory.NEWS)
    ev = _make_evidence(sub_question_id=sq.id)
    primary = _FakeGateway(evidence=[ev])
    fallback = _FakeGateway()
    critic = _FakeCritic(satisfied=True)
    
    result = _build_use_case(router, primary, fallback, primary_tool="news_api", critic=critic).execute(sq)
    
    assert primary.call_count == 1
    assert critic.call_count == 1
    assert fallback.call_count == 0
    assert result.fallback_used is False
    assert result.resolved is True

def test_news_api_fails_fallback_succeeds(router: RouteToolUseCase) -> None:
    sq = _sq("Latest news on AI", category=ToolCategory.NEWS)
    fallback_ev = _make_evidence(sub_question_id=sq.id, content="fallback")
    primary = _FakeGateway(error=RuntimeError("timeout"))
    fallback = _FakeGateway(evidence=[fallback_ev])
    
    result = _build_use_case(router, primary, fallback, primary_tool="news_api").execute(sq)
    
    assert primary.call_count == 1
    assert fallback.call_count == 1
    assert result.fallback_used is True
    assert result.resolved is True
    assert result.attempts[1].fallback_used is True
    assert result.evidence == [fallback_ev]

def test_news_api_and_fallback_fail(router: RouteToolUseCase) -> None:
    sq = _sq("Latest news on AI", category=ToolCategory.NEWS)
    primary = _FakeGateway(error=RuntimeError("primary down"))
    fallback = _FakeGateway(error=RuntimeError("fallback down"))
    
    result = _build_use_case(router, primary, fallback, primary_tool="news_api").execute(sq)
    
    assert result.resolved is False
    assert result.evidence == []
    assert len(result.attempts) == 2

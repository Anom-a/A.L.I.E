"""RetrieveEvidenceUseCase — retrieval + fallback state machine.

Orchestrates the two-stage retrieval contract for a single
:class:`SubQuestion`:

1. **Route** — use the Phase 3 router to determine the primary tool.
2. **Primary call** — invoke the selected :class:`SearchToolPort` exactly once.
3. **Fallback** — if the primary call fails *or* returns empty evidence,
   invoke the fallback gateway (Tavily) exactly once.
4. **Result** — return a :class:`RetrievalResult` with full attempt history.

Call-count guarantees per SubQuestion:

    Best case:   1 primary call, 0 fallback calls   = 1 total
    Failure:     1 primary call, 1 fallback call     = 2 total
    Maximum:     2 total — never more

The use case holds no gateway references by name.  Concrete implementations are
injected as a ``gateways`` map (keyed by the stable tool identifier from Phase
3) and a separate ``fallback_gateway``.  No SDK, HTTP, or provider detail is
imported.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional
from uuid import UUID

from application.use_cases.route_tool import RouteToolUseCase, RoutingError
from domain.entities.evidence import Evidence
from domain.entities.sub_question import SubQuestion
from domain.entities.tool_call_attempt import ToolCallAttempt
from domain.ports.search_tool_port import SearchToolPort


# ---------------------------------------------------------------------------
# Result value object
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """The outcome of retrieving evidence for one sub-question.

    Attributes:
        sub_question_id: Identity of the sub-question being researched.
        evidence: Evidence gathered (may be empty if unresolved).
        primary_tool: The tool identifier selected by the router.
        fallback_used: ``True`` if the fallback gateway was invoked.
        resolved: ``True`` if usable evidence was obtained.
        attempts: Ordered list of every gateway invocation made.
    """

    sub_question_id: UUID
    evidence: list[Evidence]
    primary_tool: str
    fallback_used: bool
    resolved: bool
    attempts: list[ToolCallAttempt]


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class RetrievalError(Exception):
    """Raised when retrieval cannot proceed due to a configuration problem."""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FALLBACK_TOOL_NAME: str = "tavily"


# ---------------------------------------------------------------------------
# Use case
# ---------------------------------------------------------------------------

class RetrieveEvidenceUseCase:
    """Execute the retrieval + fallback state machine for one SubQuestion.

    The use case is deliberately thin: route → primary call → optional fallback
    → return result.  It holds no gateway references by provider name, performs
    no I/O of its own, and can be fully exercised with fake gateways.
    """

    def __init__(
        self,
        router: RouteToolUseCase,
        gateways: dict[str, SearchToolPort],
        fallback_gateway: SearchToolPort,
        *,
        clock: Optional[Callable[[], datetime]] = None,
    ) -> None:
        """Wire the retrieval use case.

        Args:
            router: The Phase 3 router that determines which tool to use.
            gateways: Map of tool identifier → gateway implementation.
            fallback_gateway: The gateway used when the primary tool fails
                or returns empty evidence.
            clock: Source of timestamps for :class:`ToolCallAttempt` records.
        """
        self._router = router
        self._gateways = gateways
        self._fallback_gateway = fallback_gateway
        self._clock = clock if clock is not None else _utc_now

    def execute(self, sub_question: SubQuestion) -> RetrievalResult:
        """Retrieve evidence for *sub_question*.

        Returns:
            A :class:`RetrievalResult` containing evidence, attempt history,
            and resolution status.

        Raises:
            RetrievalError: If routing fails or the configured gateway is
                missing from the injected gateway map, or if the input is invalid.
        """
        if not isinstance(sub_question, SubQuestion):
            raise RetrievalError(
                f"execute() expects a SubQuestion, got {type(sub_question).__name__}"
            )

        # --- Route -------------------------------------------------------
        try:
            routed = self._router.execute(sub_question)
        except RoutingError as exc:
            raise RetrievalError(
                f"routing failed for sub-question {sub_question.id}: {exc}"
            ) from exc

        tool_name = routed.tool_name
        gateway = self._gateways.get(tool_name)
        if gateway is None:
            raise RetrievalError(
                f"no gateway registered for tool {tool_name!r}"
            )

        attempts: list[ToolCallAttempt] = []

        # --- Primary call (at most once) ---------------------------------
        primary_evidence = self._try_search(
            gateway=gateway,
            tool_name=tool_name,
            sub_question=sub_question,
            fallback_used=False,
            attempts=attempts,
        )

        if primary_evidence:
            return RetrievalResult(
                sub_question_id=sub_question.id,
                evidence=primary_evidence,
                primary_tool=tool_name,
                fallback_used=False,
                resolved=True,
                attempts=attempts,
            )

        # --- Fallback call (at most once) --------------------------------
        fallback_evidence = self._try_search(
            gateway=self._fallback_gateway,
            tool_name=FALLBACK_TOOL_NAME,
            sub_question=sub_question,
            fallback_used=True,
            attempts=attempts,
        )

        return RetrievalResult(
            sub_question_id=sub_question.id,
            evidence=fallback_evidence,
            primary_tool=tool_name,
            fallback_used=True,
            resolved=bool(fallback_evidence),
            attempts=attempts,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _try_search(
        self,
        *,
        gateway: SearchToolPort,
        tool_name: str,
        sub_question: SubQuestion,
        fallback_used: bool,
        attempts: list[ToolCallAttempt],
    ) -> list[Evidence]:
        """Call *gateway* once, record the attempt, return evidence or ``[]``."""
        try:
            evidence = gateway.search(sub_question)
            succeeded = bool(evidence)
        except Exception:  # noqa: BLE001 - deliberate adapter boundary
            evidence = []
            succeeded = False

        attempts.append(
            ToolCallAttempt(
                tool_name=tool_name,
                sub_question_id=sub_question.id,
                succeeded=succeeded,
                fallback_used=fallback_used,
                timestamp=self._clock(),
            )
        )
        return evidence


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

"""RouteToolUseCase — two-stage router for sub-questions.

Stage 1 — **classify**: determine which :class:`ToolCategory` a
:class:`SubQuestion` belongs to by delegating to an injected
:class:`SubQuestionClassifier`.  If the sub-question already carries an
explicit (non-GENERAL) category, the classifier is skipped and the existing
category is preserved.

Stage 2 — **lookup**: resolve the category to a stable tool identifier via
the hardcoded :data:`CATEGORY_TO_TOOL` mapping.

The result is a :class:`RoutedTool` value object that packages the original
sub-question id, the resolved category, and the tool name — nothing else.

No gateway is instantiated.  No HTTP call is made.  No external SDK is
imported.  The router's *only* job is to decide where a sub-question should go;
retrieval happens in a later phase.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from application.classifiers.sub_question_classifier import SubQuestionClassifier
from domain.entities.sub_question import SubQuestion
from domain.value_objects.tool_category import ToolCategory


# ---------------------------------------------------------------------------
# Routing table — one tool per category, centralised.
# ---------------------------------------------------------------------------

CATEGORY_TO_TOOL: dict[ToolCategory, str] = {
    ToolCategory.REPAIR: "ifixit",
    ToolCategory.ACADEMIC: "semantic_scholar",
    ToolCategory.NEWS: "news_api",
    ToolCategory.GENERAL: "tavily",
}


# ---------------------------------------------------------------------------
# Result value object
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RoutedTool:
    """The outcome of routing one sub-question.

    Attributes:
        sub_question_id: Identity of the routed :class:`SubQuestion`.
        category: The resolved :class:`ToolCategory` (may differ from the
            original if the classifier reclassified a ``GENERAL`` question).
        tool_name: The stable tool identifier (e.g. ``"tavily"``).
    """

    sub_question_id: UUID
    category: ToolCategory
    tool_name: str


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class RoutingError(Exception):
    """Raised when routing cannot complete for a sub-question."""


# ---------------------------------------------------------------------------
# Use case
# ---------------------------------------------------------------------------

class RouteToolUseCase:
    """Decide which research tool should handle a given :class:`SubQuestion`.

    The use case is deliberately thin: classify → lookup → return.  It holds
    no gateway references, performs no I/O, and can be fully exercised without
    network access.
    """

    def __init__(self, classifier: SubQuestionClassifier) -> None:
        """Wire the router.

        Args:
            classifier: Any :class:`SubQuestionClassifier` implementation.
                The concrete classifier is injected from outside; this class
                never constructs one.
        """
        self._classifier = classifier

    def execute(self, sub_question: SubQuestion) -> RoutedTool:
        """Route *sub_question* to a tool.

        Args:
            sub_question: A domain sub-question to classify and route.

        Returns:
            A :class:`RoutedTool` containing the resolved category and tool.

        Raises:
            RoutingError: If the sub-question is invalid, classification fails,
                or the resolved category has no tool mapping.
        """
        if not isinstance(sub_question, SubQuestion):
            raise RoutingError(
                f"expected a SubQuestion, got {type(sub_question).__name__}"
            )

        # Stage 1 — classify.
        category = self._classify(sub_question)

        # Stage 2 — hardcoded lookup.
        tool_name = self._resolve_tool(category)

        return RoutedTool(
            sub_question_id=sub_question.id,
            category=category,
            tool_name=tool_name,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _classify(self, sub_question: SubQuestion) -> ToolCategory:
        """Return the category — skip the classifier when one is explicit."""
        if sub_question.category is not ToolCategory.GENERAL:
            return sub_question.category

        try:
            return self._classifier.classify(sub_question)
        except Exception as exc:
            raise RoutingError(
                f"classifier failed for sub-question {sub_question.id}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

    @staticmethod
    def _resolve_tool(category: ToolCategory) -> str:
        """Map *category* to a tool identifier, or raise on missing entry."""
        try:
            return CATEGORY_TO_TOOL[category]
        except KeyError:
            raise RoutingError(
                f"no tool mapping for category {category!r}"
            ) from None

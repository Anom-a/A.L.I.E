"""Unit tests for :class:`RouteToolUseCase`.

All tests are deterministic — no network, no LLM, no external API.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from application.classifiers.keyword_classifier import KeywordSubQuestionClassifier
from application.classifiers.sub_question_classifier import SubQuestionClassifier
from application.use_cases.route_tool import (
    CATEGORY_TO_TOOL,
    RoutedTool,
    RouteToolUseCase,
    RoutingError,
)
from domain.entities.sub_question import SubQuestion
from domain.value_objects.tool_category import ToolCategory


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _sq(text: str, category: ToolCategory = ToolCategory.GENERAL) -> SubQuestion:
    """Convenience factory for a sub-question."""
    return SubQuestion(
        research_query_id=uuid4(),
        text=text,
        category=category,
    )


@pytest.fixture()
def mock_classifier() -> MagicMock:
    """A mock classifier with a configurable return value."""
    mock = MagicMock(spec=SubQuestionClassifier)
    mock.classify.return_value = ToolCategory.GENERAL
    return mock


@pytest.fixture()
def keyword_classifier() -> KeywordSubQuestionClassifier:
    return KeywordSubQuestionClassifier()


@pytest.fixture()
def router(keyword_classifier: KeywordSubQuestionClassifier) -> RouteToolUseCase:
    return RouteToolUseCase(classifier=keyword_classifier)


@pytest.fixture()
def mock_router(mock_classifier: MagicMock) -> RouteToolUseCase:
    return RouteToolUseCase(classifier=mock_classifier)


# ---------------------------------------------------------------------------
# 1. GENERAL classified correctly
# ---------------------------------------------------------------------------

def test_general_classified_correctly(router: RouteToolUseCase) -> None:
    result = router.execute(_sq("What are the main causes of database deadlocks?"))
    assert result.category == ToolCategory.GENERAL
    assert result.tool_name == "tavily"


# ---------------------------------------------------------------------------
# 2. REPAIR maps to ifixit
# ---------------------------------------------------------------------------

def test_repair_maps_to_ifixit(router: RouteToolUseCase) -> None:
    result = router.execute(_sq("How to repair an iPhone screen?"))
    assert result.category == ToolCategory.REPAIR
    assert result.tool_name == "ifixit"


# ---------------------------------------------------------------------------
# 3. ACADEMIC maps to semantic_scholar
# ---------------------------------------------------------------------------

def test_academic_maps_to_semantic_scholar(router: RouteToolUseCase) -> None:
    result = router.execute(_sq("What are the best scholarly studies on flaky tests?"))
    assert result.category == ToolCategory.ACADEMIC
    assert result.tool_name == "semantic_scholar"


# ---------------------------------------------------------------------------
# 4. NEWS maps to news_api
# ---------------------------------------------------------------------------

def test_news_maps_to_news_api(router: RouteToolUseCase) -> None:
    result = router.execute(_sq("What happened in AI news today?"))
    assert result.category == ToolCategory.NEWS
    assert result.tool_name == "news_api"


# ---------------------------------------------------------------------------
# 5. GENERAL maps to tavily
# ---------------------------------------------------------------------------

def test_general_maps_to_tavily(router: RouteToolUseCase) -> None:
    result = router.execute(_sq("Explain the difference between TCP and UDP"))
    assert result.category == ToolCategory.GENERAL
    assert result.tool_name == "tavily"


# ---------------------------------------------------------------------------
# 6. Explicit non-GENERAL category is preserved
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "category,expected_tool",
    [
        (ToolCategory.REPAIR, "ifixit"),
        (ToolCategory.ACADEMIC, "semantic_scholar"),
        (ToolCategory.NEWS, "news_api"),
    ],
)
def test_explicit_category_preserved(
    mock_router: RouteToolUseCase,
    mock_classifier: MagicMock,
    category: ToolCategory,
    expected_tool: str,
) -> None:
    """When a sub-question has an explicit non-GENERAL category, the router
    preserves it and does not invoke the classifier."""
    sq = _sq("Anything at all", category=category)
    result = mock_router.execute(sq)

    assert result.category == category
    assert result.tool_name == expected_tool
    mock_classifier.classify.assert_not_called()


# ---------------------------------------------------------------------------
# 7. Classifier is called only when category is GENERAL
# ---------------------------------------------------------------------------

def test_classifier_called_for_general(
    mock_router: RouteToolUseCase, mock_classifier: MagicMock
) -> None:
    sq = _sq("Some generic question", category=ToolCategory.GENERAL)
    mock_router.execute(sq)
    mock_classifier.classify.assert_called_once_with(sq)


def test_classifier_not_called_for_non_general(
    mock_router: RouteToolUseCase, mock_classifier: MagicMock
) -> None:
    sq = _sq("Something about repair", category=ToolCategory.REPAIR)
    mock_router.execute(sq)
    mock_classifier.classify.assert_not_called()


# ---------------------------------------------------------------------------
# 8. Unsupported category raises RoutingError
# ---------------------------------------------------------------------------

def test_unsupported_category_raises_routing_error(
    mock_classifier: MagicMock,
) -> None:
    """If the classifier returns an unknown category, routing fails."""
    # Simulate a category not in CATEGORY_TO_TOOL by monkeypatching the table.
    # Since all four categories are already mapped, we test the code path by
    # having the classifier return a mock category.
    fake_category = MagicMock()
    fake_category.__repr__ = lambda _: "FakeCategory"
    mock_classifier.classify.return_value = fake_category

    router = RouteToolUseCase(classifier=mock_classifier)
    sq = _sq("Something weird")

    with pytest.raises(RoutingError, match="no tool mapping for category"):
        router.execute(sq)


# ---------------------------------------------------------------------------
# 9. Every supported ToolCategory has exactly one mapping
# ---------------------------------------------------------------------------

def test_every_category_has_one_tool() -> None:
    """The routing table must have exactly one entry per ToolCategory member."""
    categories = set(ToolCategory)
    mapped_categories = set(CATEGORY_TO_TOOL.keys())
    assert mapped_categories == categories, (
        f"Routing table mismatch. "
        f"Missing: {categories - mapped_categories}. "
        f"Extra: {mapped_categories - categories}."
    )


def test_routing_table_has_no_duplicate_tools() -> None:
    """Each tool should appear at most once in the routing table."""
    tools = list(CATEGORY_TO_TOOL.values())
    assert len(tools) == len(set(tools)), (
        f"Duplicate tool names in CATEGORY_TO_TOOL: {tools}"
    )


def test_routing_table_size_matches_category_count() -> None:
    """Invariant: len(CATEGORY_TO_TOOL) == number of ToolCategory members."""
    assert len(CATEGORY_TO_TOOL) == len(ToolCategory)


# ---------------------------------------------------------------------------
# Result value object
# ---------------------------------------------------------------------------

def test_routed_tool_fields(router: RouteToolUseCase) -> None:
    sq = _sq("How to repair a bike?")
    result = router.execute(sq)

    assert isinstance(result, RoutedTool)
    assert result.sub_question_id == sq.id
    assert result.category == ToolCategory.REPAIR
    assert result.tool_name == "ifixit"


def test_routed_tool_is_frozen() -> None:
    tool = RoutedTool(
        sub_question_id=uuid4(),
        category=ToolCategory.GENERAL,
        tool_name="tavily",
    )
    with pytest.raises(AttributeError):
        tool.tool_name = "something_else"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Classifier failure handling
# ---------------------------------------------------------------------------

def test_classifier_exception_wrapped_in_routing_error(
    mock_classifier: MagicMock,
) -> None:
    mock_classifier.classify.side_effect = ValueError("boom")
    router = RouteToolUseCase(classifier=mock_classifier)
    sq = _sq("Something")

    with pytest.raises(RoutingError, match="classifier failed"):
        router.execute(sq)


# ---------------------------------------------------------------------------
# Invalid input
# ---------------------------------------------------------------------------

def test_non_sub_question_raises_routing_error(
    router: RouteToolUseCase,
) -> None:
    with pytest.raises(RoutingError, match="expected a SubQuestion"):
        router.execute("not a SubQuestion")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Architecture guard — no forbidden imports
# ---------------------------------------------------------------------------

def test_route_tool_module_has_no_forbidden_imports() -> None:
    """RouteToolUseCase must not import any concrete gateway or SDK."""
    import application.use_cases.route_tool as mod
    import inspect

    source = inspect.getsource(mod)
    forbidden = [
        "tavily", "openai", "ifixit", "semantic_scholar",
        "news_api", "fastapi", "langgraph", "httpx", "dotenv",
    ]
    # Check imports only — not string literals like "tavily" in the mapping.
    import_lines = [
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    for imp in import_lines:
        for name in forbidden:
            assert name not in imp.lower(), (
                f"Forbidden import {name!r} found in route_tool.py: {imp}"
            )

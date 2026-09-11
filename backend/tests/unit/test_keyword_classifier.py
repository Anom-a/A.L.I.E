"""Unit tests for :class:`KeywordSubQuestionClassifier`.

The classifier's precedence order is:

    NEWS  →  ACADEMIC  →  REPAIR  →  GENERAL

All tests are deterministic — no network, no LLM, no external API.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from application.classifiers.keyword_classifier import KeywordSubQuestionClassifier
from domain.entities.sub_question import SubQuestion
from domain.value_objects.tool_category import ToolCategory


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def classifier() -> KeywordSubQuestionClassifier:
    return KeywordSubQuestionClassifier()


def _sq(text: str) -> SubQuestion:
    """Convenience factory for a GENERAL sub-question with the given text."""
    return SubQuestion(
        research_query_id=uuid4(),
        text=text,
        category=ToolCategory.GENERAL,
    )


# ---------------------------------------------------------------------------
# 1. REPAIR keyword maps to REPAIR
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "How to repair an iPhone screen?",
        "Fix a leaking faucet",
        "Troubleshoot a black screen on a MacBook",
        "Complete teardown of a PS5 controller",
        "Battery replacement guide for Galaxy S21",
        "Disassembly instructions for a Dyson vacuum",
        "My laptop keyboard is broken",
        "Scheduled maintenance for an HP printer",
    ],
)
def test_repair_keywords(classifier: KeywordSubQuestionClassifier, text: str) -> None:
    assert classifier.classify(_sq(text)) == ToolCategory.REPAIR


# ---------------------------------------------------------------------------
# 2. Multiple repair keywords still map to REPAIR
# ---------------------------------------------------------------------------

def test_multiple_repair_keywords(classifier: KeywordSubQuestionClassifier) -> None:
    result = classifier.classify(
        _sq("How to repair and fix a broken screen during teardown?")
    )
    assert result == ToolCategory.REPAIR


# ---------------------------------------------------------------------------
# 3. ACADEMIC keyword maps to ACADEMIC
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "Find research paper on quantum computing",
        "Scholarly articles on CRISPR gene editing",
        "What do academic studies say about remote work?",
        "Study on the effects of sleep deprivation",
        "Best journal articles about machine learning",
        "Literature review on climate change models",
        "Citation analysis for PageRank paper",
        "Scientific discoveries in astrophysics over the decade",
    ],
)
def test_academic_keywords(classifier: KeywordSubQuestionClassifier, text: str) -> None:
    assert classifier.classify(_sq(text)) == ToolCategory.ACADEMIC


# ---------------------------------------------------------------------------
# 4. NEWS keyword maps to NEWS
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "What is the latest in AI regulation?",
        "Recent developments in space exploration",
        "What happened today in financial markets?",
        "Yesterday's tech announcements",
        "Breaking coverage of the summit",
        "Top news stories this week",
        "Current events in European politics",
    ],
)
def test_news_keywords(classifier: KeywordSubQuestionClassifier, text: str) -> None:
    assert classifier.classify(_sq(text)) == ToolCategory.NEWS


# ---------------------------------------------------------------------------
# 5. Unrelated question maps to GENERAL
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "What are the main causes of database deadlocks?",
        "Explain the difference between TCP and UDP",
        "How does a hash table work?",
        "Best practices for writing clean code",
    ],
)
def test_general_fallback(classifier: KeywordSubQuestionClassifier, text: str) -> None:
    assert classifier.classify(_sq(text)) == ToolCategory.GENERAL


# ---------------------------------------------------------------------------
# 6. Case-insensitive matching
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text,expected",
    [
        ("REPAIR a phone screen", ToolCategory.REPAIR),
        ("SCHOLARLY articles on AI", ToolCategory.ACADEMIC),
        ("LATEST in tech", ToolCategory.NEWS),
        ("How To Fix A Bike", ToolCategory.REPAIR),
        ("Research Paper On ML", ToolCategory.ACADEMIC),
        ("BREAKING News", ToolCategory.NEWS),
    ],
)
def test_case_insensitive(
    classifier: KeywordSubQuestionClassifier, text: str, expected: ToolCategory
) -> None:
    assert classifier.classify(_sq(text)) == expected


# ---------------------------------------------------------------------------
# 7. Whitespace normalisation
# ---------------------------------------------------------------------------

def test_whitespace_normalisation(classifier: KeywordSubQuestionClassifier) -> None:
    # Extra spaces, tabs, newlines — all collapsed before matching.
    result = classifier.classify(
        _sq("How  to\t\trepair\n\na   broken   phone?")
    )
    assert result == ToolCategory.REPAIR


def test_leading_trailing_whitespace(
    classifier: KeywordSubQuestionClassifier,
) -> None:
    result = classifier.classify(_sq("   fix the screen   "))
    assert result == ToolCategory.REPAIR


# ---------------------------------------------------------------------------
# 8. Mixed keywords — deterministic precedence
# ---------------------------------------------------------------------------
# Precedence: NEWS > ACADEMIC > REPAIR > GENERAL

def test_news_beats_academic(classifier: KeywordSubQuestionClassifier) -> None:
    """NEWS takes precedence over ACADEMIC when both keywords are present."""
    result = classifier.classify(
        _sq("Latest research paper on quantum computing")
    )
    assert result == ToolCategory.NEWS


def test_news_beats_repair(classifier: KeywordSubQuestionClassifier) -> None:
    """NEWS takes precedence over REPAIR."""
    result = classifier.classify(
        _sq("Breaking news about phone repair services")
    )
    assert result == ToolCategory.NEWS


def test_academic_beats_repair(classifier: KeywordSubQuestionClassifier) -> None:
    """ACADEMIC takes precedence over REPAIR."""
    result = classifier.classify(
        _sq("Research paper on phone repair techniques")
    )
    assert result == ToolCategory.ACADEMIC


def test_all_categories_present(classifier: KeywordSubQuestionClassifier) -> None:
    """When keywords from NEWS, ACADEMIC, and REPAIR all appear, NEWS wins."""
    result = classifier.classify(
        _sq("Latest scholarly study on troubleshoot techniques")
    )
    assert result == ToolCategory.NEWS


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------

def test_classifier_satisfies_protocol() -> None:
    """KeywordSubQuestionClassifier structurally satisfies SubQuestionClassifier."""
    from application.classifiers.sub_question_classifier import SubQuestionClassifier

    assert isinstance(KeywordSubQuestionClassifier(), SubQuestionClassifier)

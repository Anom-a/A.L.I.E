"""KeywordSubQuestionClassifier — deterministic keyword-based classifier.

Phase 3's first concrete :class:`SubQuestionClassifier`.  It scans the
sub-question text for category-specific keywords and returns the highest-
priority match, falling back to :pydata:`ToolCategory.GENERAL` when no keyword
matches.

Precedence order (highest → lowest):

    NEWS  →  ACADEMIC  →  REPAIR  →  GENERAL

The order is explicit and documented so that tests can rely on it.  A question
containing keywords from multiple categories is classified by whichever
category appears first in the precedence list.

Implementation notes
--------------------
* Uses only the Python standard library — no NLP, no ML, no external deps.
* Matching is **case-insensitive** and **whitespace-normalised** (runs of
  whitespace are collapsed to a single space before scanning).
* A keyword matches if it appears as a *substring* of the normalised text.
  This is intentionally generous: ``"repair"`` matches ``"repairing"`` and
  ``"irreparable"``.  A future LLM classifier can be more precise.
"""

from __future__ import annotations

from domain.entities.sub_question import SubQuestion
from domain.value_objects.tool_category import ToolCategory


# ---------------------------------------------------------------------------
# Keyword sets — lowercase, ready for case-insensitive substring matching.
# ---------------------------------------------------------------------------

_NEWS_KEYWORDS: frozenset[str] = frozenset(
    {
        "latest",
        "recent",
        "today",
        "yesterday",
        "breaking",
        "news",
        "current events",
    }
)

_ACADEMIC_KEYWORDS: frozenset[str] = frozenset(
    {
        "research paper",
        "paper",
        "scholarly",
        "academic",
        "study",
        "journal",
        "literature",
        "citation",
        "scientific",
    }
)

_REPAIR_KEYWORDS: frozenset[str] = frozenset(
    {
        "repair",
        "fix",
        "troubleshoot",
        "teardown",
        "replacement",
        "disassembly",
        "broken",
        "maintenance",
    }
)

# Ordered from highest to lowest priority.
_PRECEDENCE: tuple[tuple[ToolCategory, frozenset[str]], ...] = (
    (ToolCategory.NEWS, _NEWS_KEYWORDS),
    (ToolCategory.ACADEMIC, _ACADEMIC_KEYWORDS),
    (ToolCategory.REPAIR, _REPAIR_KEYWORDS),
)


class KeywordSubQuestionClassifier:
    """Classify a :class:`SubQuestion` using deterministic keyword matching.

    Precedence (descending): NEWS → ACADEMIC → REPAIR → GENERAL.
    """

    def classify(self, sub_question: SubQuestion) -> ToolCategory:
        """Return the highest-precedence category whose keywords appear in
        the sub-question text, or :pydata:`ToolCategory.GENERAL` if none match.
        """
        normalised = _normalise(sub_question.text)
        for category, keywords in _PRECEDENCE:
            if _any_keyword_matches(normalised, keywords):
                return category
        return ToolCategory.GENERAL


def _normalise(text: str) -> str:
    """Lowercase and collapse whitespace for uniform matching."""
    return " ".join(text.lower().split())


def _any_keyword_matches(text: str, keywords: frozenset[str]) -> bool:
    """Return ``True`` if any keyword in *keywords* is a substring of *text*."""
    return any(kw in text for kw in keywords)

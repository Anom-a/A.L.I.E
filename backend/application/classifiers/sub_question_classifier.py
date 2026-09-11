"""SubQuestionClassifier — abstraction for categorising a sub-question.

This protocol defines the *single method* that the router depends on.  Any
implementation — a keyword heuristic, an LLM classifier, or a future ML model —
can satisfy it, so the router never needs to change when the classification
strategy is swapped.

The protocol speaks only in domain types: :class:`SubQuestion` in,
:class:`ToolCategory` out.  No I/O, no SDK imports, no network calls.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.entities.sub_question import SubQuestion
from domain.value_objects.tool_category import ToolCategory


@runtime_checkable
class SubQuestionClassifier(Protocol):
    """Determine the :class:`ToolCategory` for a given :class:`SubQuestion`."""

    def classify(self, sub_question: SubQuestion) -> ToolCategory:
        """Return the most appropriate category for *sub_question*.

        Implementations must be deterministic *within a single execution*
        (i.e. same input → same output) so that routing stays predictable.
        """
        ...

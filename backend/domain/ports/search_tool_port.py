"""SearchToolPort: the contract for a research/search tool.

A search tool takes a domain :class:`SubQuestion` and returns domain
:class:`Evidence`. The interface speaks purely in domain types — no HTTP
requests, response objects, or provider-specific payloads leak across this
boundary. Concrete tools (web search, academic search, …) implement this in a
later phase.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from domain.entities.evidence import Evidence
from domain.entities.sub_question import SubQuestion


@runtime_checkable
class SearchToolPort(Protocol):
    """Abstraction over a tool that gathers evidence for a sub-question."""

    def search(self, sub_question: SubQuestion) -> list[Evidence]:
        """Return the evidence found for ``sub_question`` (possibly empty)."""
        ...

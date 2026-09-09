"""Report: the final synthesised research result.

A report is composed of ordered :class:`ReportSection` values plus the set of
:class:`Citation` records the report draws on. The section representation is
deliberately framework-independent — plain text content plus references to
citations by their source identifier — so the domain is not tied to any future
JSON schema, markdown renderer, or HTTP serialisation.

Key invariant: a report must contain at least one citation, and every citation
a section references must be present in the report's citation set.

This module does no synthesis, rendering, or serialisation — those are
outer-layer concerns for a later phase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from domain.entities.citation import Citation
from domain.exceptions import InvalidDomainValue


@dataclass(frozen=True, slots=True)
class ReportSection:
    """One section of a report: a heading, prose, and citation references.

    ``citation_ids`` refer to citations by their ``source_url_or_id``. Storing
    references (rather than embedding citation objects) keeps sections light and
    lets the owning :class:`Report` hold the single source of truth for
    provenance.
    """

    title: str
    content: str
    citation_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise InvalidDomainValue("ReportSection title must not be empty")
        if not self.content or not self.content.strip():
            raise InvalidDomainValue("ReportSection content must not be empty")
        # Normalise any input sequence to an immutable tuple.
        object.__setattr__(self, "citation_ids", tuple(self.citation_ids))
        if any(not cid or not cid.strip() for cid in self.citation_ids):
            raise InvalidDomainValue(
                "ReportSection citation_ids must not contain empty values"
            )


@dataclass(frozen=True, slots=True)
class Report:
    """The synthesised result of a research query."""

    query_id: UUID
    sections: tuple[ReportSection, ...]
    citations: tuple[Citation, ...]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not isinstance(self.query_id, UUID):
            raise InvalidDomainValue("Report query_id must be a UUID")
        # Normalise input sequences to immutable tuples.
        object.__setattr__(self, "sections", tuple(self.sections))
        object.__setattr__(self, "citations", tuple(self.citations))
        if not isinstance(self.generated_at, datetime):
            raise InvalidDomainValue("Report generated_at must be a datetime")

        if any(not isinstance(section, ReportSection) for section in self.sections):
            raise InvalidDomainValue("Report sections must all be ReportSection values")
        if any(not isinstance(citation, Citation) for citation in self.citations):
            raise InvalidDomainValue("Report citations must all be Citation values")

        if len(self.citations) < 1:
            raise InvalidDomainValue("Report must contain at least one citation")

        # Referential integrity: a section may only cite sources the report holds.
        known_ids = {citation.source_url_or_id for citation in self.citations}
        for section in self.sections:
            unknown = set(section.citation_ids) - known_ids
            if unknown:
                raise InvalidDomainValue(
                    "Report section references unknown citation ids: "
                    f"{sorted(unknown)}"
                )

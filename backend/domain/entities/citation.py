"""Citation: provenance for a piece of evidence (and later, report claims).

A citation records *where* a fact came from at the moment it was retrieved. It
is an immutable record of provenance: the domain never synthesises URLs or
source metadata — it only preserves what an outer layer supplied. Because it is
a pure value object, two citations with the same fields are considered equal.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.exceptions import InvalidDomainValue


@dataclass(frozen=True, slots=True)
class Citation:
    """Immutable provenance record for retrieved information."""

    source_url_or_id: str
    source_name: str
    retrieved_at: datetime

    def __post_init__(self) -> None:
        if not self.source_url_or_id or not self.source_url_or_id.strip():
            raise InvalidDomainValue("Citation source_url_or_id must not be empty")
        if not self.source_name or not self.source_name.strip():
            raise InvalidDomainValue("Citation source_name must not be empty")
        if not isinstance(self.retrieved_at, datetime):
            raise InvalidDomainValue("Citation retrieved_at must be a datetime")

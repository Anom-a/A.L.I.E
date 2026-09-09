"""Evidence: retrieved information with provenance.

Evidence is a piece of content gathered while researching a sub-question,
always paired with a :class:`Citation` so its origin is never lost. The
``source_type`` records the *kind* of source it came from; it is an explicit
domain enum rather than a free string so outer layers can reason about
provenance without parsing text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

from domain.entities.citation import Citation
from domain.exceptions import InvalidDomainValue


class SourceType(Enum):
    """The kind of source a piece of evidence was drawn from."""

    WEB = "web"
    ACADEMIC = "academic"
    NEWS = "news"
    DOCUMENTATION = "documentation"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Evidence:
    """A retrieved fact with its provenance."""

    sub_question_id: UUID
    source_type: SourceType
    content: str
    citation: Citation
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not isinstance(self.sub_question_id, UUID):
            raise InvalidDomainValue("Evidence sub_question_id must be a UUID")
        if not isinstance(self.source_type, SourceType):
            raise InvalidDomainValue("Evidence source_type must be a SourceType member")
        if not self.content or not self.content.strip():
            raise InvalidDomainValue("Evidence content must not be empty")
        if not isinstance(self.citation, Citation):
            raise InvalidDomainValue("Evidence citation must be a Citation")
        if not isinstance(self.id, UUID):
            raise InvalidDomainValue("Evidence id must be a UUID")

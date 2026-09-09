"""ResearchQuery: the original user research request.

This is the root of a research job. It captures what the user asked, when, and
the lifecycle status of the request. Phase 0 models the entity and its
invariants only — there is no persistence, no state-transition machinery, and
no I/O. Status transitions will be driven by use cases in a later phase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from domain.exceptions import InvalidDomainValue


class ResearchStatus(Enum):
    """Lifecycle status of a research query."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ResearchQuery:
    """A user's research request and its lifecycle status."""

    topic: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: ResearchStatus = ResearchStatus.PENDING

    def __post_init__(self) -> None:
        if not self.topic or not self.topic.strip():
            raise InvalidDomainValue("ResearchQuery topic must not be empty")
        if not isinstance(self.id, UUID):
            raise InvalidDomainValue("ResearchQuery id must be a UUID")
        if not isinstance(self.created_at, datetime):
            raise InvalidDomainValue("ResearchQuery created_at must be a datetime")
        if not isinstance(self.status, ResearchStatus):
            raise InvalidDomainValue(
                "ResearchQuery status must be a ResearchStatus member"
            )

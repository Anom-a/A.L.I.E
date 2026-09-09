"""ResearchJobRepositoryPort: the minimal persistence contract for a job.

The future asynchronous REST workflow needs to (1) store a research job, (2)
fetch it by id, and (3) update its lifecycle state. That is the whole contract
— nothing more is defined until a use case actually needs it. A
:class:`ResearchQuery` is the job's root; the concrete store (in-memory, SQL,
Redis, …) is an outer-layer concern for a later phase.
"""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable
from uuid import UUID

from domain.entities.research_query import ResearchQuery, ResearchStatus


@runtime_checkable
class ResearchJobRepositoryPort(Protocol):
    """Abstraction over storage for research jobs."""

    def add(self, query: ResearchQuery) -> None:
        """Persist a new research job."""
        ...

    def get(self, query_id: UUID) -> Optional[ResearchQuery]:
        """Return the job with ``query_id``, or ``None`` if it is unknown."""
        ...

    def update_status(self, query_id: UUID, status: ResearchStatus) -> None:
        """Update the lifecycle status of an existing job."""
        ...

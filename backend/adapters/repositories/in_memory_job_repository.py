"""InMemoryJobRepository: a simple thread-safe dictionary-backed repository.

This implements both the domain `ResearchJobRepositoryPort` and the application's
`ExtendedJobRepositoryPort` for the FastAPI service, providing a place to store
queries, their lifecycle statuses, generated reports, and potential error messages.
"""

from threading import Lock
from typing import Optional
from uuid import UUID

from domain.entities.research_query import ResearchQuery, ResearchStatus
from domain.entities.report import Report
from domain.ports.job_repository_port import ResearchJobRepositoryPort
from application.use_cases.run_research import ExtendedJobRepositoryPort


class InMemoryJobRepository:
    """An in-memory store for research jobs, their reports, and errors."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._queries: dict[UUID, ResearchQuery] = {}
        self._reports: dict[UUID, Report] = {}
        self._errors: dict[UUID, str] = {}

    def add(self, query: ResearchQuery) -> None:
        """Persist a new research job."""
        with self._lock:
            self._queries[query.id] = query

    def get(self, query_id: UUID) -> Optional[ResearchQuery]:
        """Return the job with query_id, or None if unknown."""
        with self._lock:
            return self._queries.get(query_id)

    def update_status(self, query_id: UUID, status: ResearchStatus) -> None:
        """Update the lifecycle status of an existing job."""
        with self._lock:
            query = self._queries.get(query_id)
            if query:
                # We replace the frozen dataclass instance with a new one
                # carrying the updated status.
                from dataclasses import replace
                self._queries[query_id] = replace(query, status=status)

    def save_report(self, query_id: UUID, report: Report) -> None:
        """Save the generated report for a completed job."""
        with self._lock:
            self._reports[query_id] = report

    def get_report(self, query_id: UUID) -> Optional[Report]:
        """Fetch the generated report for a completed job."""
        with self._lock:
            return self._reports.get(query_id)

    def save_error(self, query_id: UUID, error: str) -> None:
        """Save an error message for a failed job."""
        with self._lock:
            self._errors[query_id] = error

    def get_error(self, query_id: UUID) -> Optional[str]:
        """Fetch the error message for a failed job."""
        with self._lock:
            return self._errors.get(query_id)

# Ensure interface satisfaction at import time
_: ResearchJobRepositoryPort = InMemoryJobRepository()
_: ExtendedJobRepositoryPort = InMemoryJobRepository()

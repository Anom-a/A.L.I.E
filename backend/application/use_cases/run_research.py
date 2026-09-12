"""RunResearchUseCase: Orchestrates the research graph and updates job status."""

from typing import Protocol, Optional
from uuid import UUID

from application.graph.research_graph import ResearchGraph
from domain.entities.research_query import ResearchQuery, ResearchStatus
from domain.entities.report import Report


class ExtendedJobRepositoryPort(Protocol):
    """Extended repository interface required by the RunResearchUseCase.
    
    Provides methods to save the final report or error message, which are
    not present in the base domain ResearchJobRepositoryPort.
    """
    
    def get(self, query_id: UUID) -> Optional[ResearchQuery]:
        """Return the job with query_id."""
        ...
        
    def update_status(self, query_id: UUID, status: ResearchStatus) -> None:
        """Update the lifecycle status of an existing job."""
        ...
        
    def save_report(self, query_id: UUID, report: Report) -> None:
        """Save the generated report for a completed job."""
        ...
        
    def save_error(self, query_id: UUID, error: str) -> None:
        """Save an error message for a failed job."""
        ...


import logging

logger = logging.getLogger("application")

class RunResearchUseCase:
    """Executes the research graph and tracks lifecycle state."""

    def __init__(
        self,
        graph: ResearchGraph,
        repository: ExtendedJobRepositoryPort,
    ) -> None:
        self._graph = graph
        self._repository = repository

    def execute(self, query_id: UUID) -> None:
        """Run the research process for a given query ID.
        
        This method is intended to be run in the background. It transitions the job
        status, invokes the graph, and stores the resulting Report or error.
        """
        query = self._repository.get(query_id)
        if not query:
            logger.warning("Research job not found", extra={"job_id": str(query_id)})
            return  # Job was not found, nothing to run

        try:
            logger.info("Research job started", extra={"job_id": str(query_id)})
            self._repository.update_status(query_id, ResearchStatus.RUNNING)
            
            report = self._graph.invoke(query)
            
            logger.info("Report completed", extra={"job_id": str(query_id)})
            self._repository.save_report(query_id, report)
            self._repository.update_status(query_id, ResearchStatus.DONE)
            
        except Exception as exc:
            # Preserve stack trace internally, save safe message externally
            logger.exception(
                "Research job failed due to an unexpected error",
                extra={"job_id": str(query_id)}
            )
            self._repository.save_error(query_id, "Research failed due to an unexpected internal error.")
            self._repository.update_status(query_id, ResearchStatus.FAILED)

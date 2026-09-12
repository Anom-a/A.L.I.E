"""Research Controller: FastAPI endpoints for research tasks."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from domain.entities.research_query import ResearchQuery, ResearchStatus
from adapters.presenters.report_presenter import ReportDTO, ReportPresenter
from application.use_cases.run_research import RunResearchUseCase, ExtendedJobRepositoryPort
from adapters.controllers.auth_controller import get_current_user
from infrastructure.db.models import User, ResearchJob
from infrastructure.db.database import get_db
from sqlalchemy.orm import Session
from domain.ports.llm_port import LLMPort
from domain.ports.search_tool_port import SearchToolPort


# --- DTOs ---

class SubmitResearchRequest(BaseModel):
    """Payload for submitting a new research query."""
    topic: str = Field(..., min_length=1)


class JobStatusResponse(BaseModel):
    """Status of a research job."""
    job_id: UUID
    status: ResearchStatus
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str


# --- Router ---
router = APIRouter()

# The dependencies will be overridden in infrastructure/api/dependencies.py
# We define stub dependables here to satisfy FastAPI injection syntax without
# hardcoding implementations.

def get_job_repository() -> ExtendedJobRepositoryPort:
    raise NotImplementedError("Overridden by DI")

def get_run_research_use_case() -> RunResearchUseCase:
    raise NotImplementedError("Overridden by DI")

def get_llm_port() -> LLMPort:
    raise NotImplementedError("Overridden by DI")

def get_search_port() -> SearchToolPort:
    raise NotImplementedError("Overridden by DI")


import logging

logger = logging.getLogger("adapters")

@router.post("/research", response_model=JobStatusResponse, status_code=202)
def submit_research(
    request: SubmitResearchRequest,
    background_tasks: BackgroundTasks,
    req: Request,
    current_user: User = Depends(get_current_user),
    repo: ExtendedJobRepositoryPort = Depends(get_job_repository),
    use_case: RunResearchUseCase = Depends(get_run_research_use_case),
):
    """Submit a new research query and start processing in the background."""
    # Pass user_id to repo manually since Depends(get_job_repository) might not have it in state yet
    repo.user_id = current_user.id

    query = ResearchQuery(topic=request.topic)
    repo.add(query)
    
    logger.info("Research job accepted", extra={"job_id": str(query.id)})
    
    # Run the graph synchronously within a background thread so we don't block
    background_tasks.add_task(use_case.execute, query.id)
    
    return JobStatusResponse(job_id=query.id, status=query.status)


@router.get("/research/{job_id}", response_model=JobStatusResponse)
def get_job_status(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    repo: ExtendedJobRepositoryPort = Depends(get_job_repository),
):
    """Poll the status of a research job."""
    query = repo.get(job_id)
    if not query:
        raise HTTPException(status_code=404, detail="Job not found")
        
    error = repo.get_error(job_id)
    return JobStatusResponse(job_id=query.id, status=query.status, error=error)


@router.get("/research", response_model=list[JobStatusResponse])
def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all past research jobs for the current user."""
    jobs = db.query(ResearchJob).filter(ResearchJob.user_id == current_user.id).order_by(ResearchJob.created_at.desc()).all()
    return [JobStatusResponse(job_id=job.id, status=job.status, error=job.error) for job in jobs]


@router.get("/research/{job_id}/report", response_model=ReportDTO)
def get_job_report(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    repo: ExtendedJobRepositoryPort = Depends(get_job_repository),
):
    """Fetch the final Report DTO. Returns 404 until status=DONE."""
    query = repo.get(job_id)
    if not query:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if query.status != ResearchStatus.DONE:
        raise HTTPException(status_code=404, detail="Report not ready")
        
    report = repo.get_report(job_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
        
    return ReportPresenter.to_dto(report)


@router.get("/health", response_model=HealthResponse)
def health_check(
    llm: LLMPort = Depends(get_llm_port),
    search: SearchToolPort = Depends(get_search_port),
):
    """Liveness and readiness check.
    
    If the dependencies resolve successfully, it means config is loaded
    and adapters are correctly instantiated.
    """
    # Simply having the ports injected proves the DI container can build them
    # without ConfigError being raised.
    return HealthResponse(status="ok")

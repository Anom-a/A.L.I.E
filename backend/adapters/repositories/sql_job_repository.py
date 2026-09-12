import json
from typing import Optional
from uuid import UUID
from dataclasses import asdict

from sqlalchemy.orm import Session

from domain.entities.research_query import ResearchQuery, ResearchStatus
from domain.entities.report import Report, ReportSection
from domain.entities.citation import Citation
from application.use_cases.run_research import ExtendedJobRepositoryPort
from infrastructure.db.models import ResearchJob
from infrastructure.db.database import SessionLocal

class SQLJobRepository(ExtendedJobRepositoryPort):
    def __init__(self, user_id: Optional[UUID] = None):
        self.user_id = user_id
        # We use a fresh session for each operation to support background tasks safely
    
    def _get_session(self) -> Session:
        return SessionLocal()

    def add(self, query: ResearchQuery) -> None:
        if not self.user_id:
            raise ValueError("user_id must be provided to save a new job")
            
        with self._get_session() as db:
            job = ResearchJob(
                id=query.id,
                user_id=self.user_id,
                topic=query.topic,
                status=query.status,
                created_at=query.created_at
            )
            db.add(job)
            db.commit()

    def get(self, query_id: UUID) -> Optional[ResearchQuery]:
        with self._get_session() as db:
            job = db.query(ResearchJob).filter(ResearchJob.id == query_id).first()
            if not job:
                return None
            return ResearchQuery(
                topic=job.topic,
                id=job.id,
                created_at=job.created_at,
                status=job.status
            )

    def update_status(self, query_id: UUID, status: ResearchStatus) -> None:
        with self._get_session() as db:
            job = db.query(ResearchJob).filter(ResearchJob.id == query_id).first()
            if job:
                job.status = status
                db.commit()

    def save_report(self, query_id: UUID, report: Report) -> None:
        with self._get_session() as db:
            job = db.query(ResearchJob).filter(ResearchJob.id == query_id).first()
            if job:
                # Serialize report to JSON dict
                sections_data = [asdict(s) for s in report.sections]
                citations_data = [asdict(c) for c in report.citations]
                
                report_dict = {
                    "query_id": str(report.query_id),
                    "sections": sections_data,
                    "citations": citations_data,
                    "generated_at": report.generated_at.isoformat()
                }
                job.report_data = report_dict
                db.commit()

    def get_report(self, query_id: UUID) -> Optional[Report]:
        with self._get_session() as db:
            job = db.query(ResearchJob).filter(ResearchJob.id == query_id).first()
            if not job or not job.report_data:
                return None
                
            data = job.report_data
            
            # Deserialize
            sections = [ReportSection(**s) for s in data["sections"]]
            citations = [Citation(**c) for c in data["citations"]]
            from datetime import datetime
            generated_at = datetime.fromisoformat(data["generated_at"])
            
            return Report(
                query_id=UUID(data["query_id"]),
                sections=tuple(sections),
                citations=tuple(citations),
                generated_at=generated_at
            )

    def save_error(self, query_id: UUID, error: str) -> None:
        with self._get_session() as db:
            job = db.query(ResearchJob).filter(ResearchJob.id == query_id).first()
            if job:
                job.error = error
                db.commit()

    def get_error(self, query_id: UUID) -> Optional[str]:
        with self._get_session() as db:
            job = db.query(ResearchJob).filter(ResearchJob.id == query_id).first()
            return job.error if job else None


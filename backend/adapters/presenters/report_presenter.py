"""ReportPresenter: maps the domain Report entity to a JSON-serializable DTO."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from domain.entities.report import Report


class CitationDTO(BaseModel):
    """Data Transfer Object for a Citation."""
    
    source_url_or_id: str
    source_name: str
    retrieved_at: datetime


class ReportSectionDTO(BaseModel):
    """Data Transfer Object for a ReportSection."""
    
    title: str
    content: str
    citation_ids: list[str]


class ReportDTO(BaseModel):
    """Data Transfer Object for a Report."""
    
    query_id: UUID
    sections: list[ReportSectionDTO]
    citations: list[CitationDTO]
    generated_at: datetime


class ReportPresenter:
    """Presenter to convert domain Report into DTOs for the HTTP API."""

    @staticmethod
    def to_dto(report: Report) -> ReportDTO:
        """Map a domain Report entity to a ReportDTO."""
        sections_dto = [
            ReportSectionDTO(
                title=s.title,
                content=s.content,
                citation_ids=list(s.citation_ids)
            )
            for s in report.sections
        ]
        
        citations_dto = [
            CitationDTO(
                source_url_or_id=c.source_url_or_id,
                source_name=c.source_name,
                retrieved_at=c.retrieved_at
            )
            for c in report.citations
        ]
        
        return ReportDTO(
            query_id=report.query_id,
            sections=sections_dto,
            citations=citations_dto,
            generated_at=report.generated_at
        )

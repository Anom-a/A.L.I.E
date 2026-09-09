"""Tests for the Report and ReportSection entities and their invariants."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.entities.citation import Citation
from domain.entities.report import Report, ReportSection
from domain.exceptions import InvalidDomainValue


def _citation(source_id: str = "id-1") -> Citation:
    return Citation(
        source_url_or_id=source_id,
        source_name="Example",
        retrieved_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )


# --- Report --------------------------------------------------------------


def test_valid_construction() -> None:
    report = Report(
        query_id=uuid4(),
        sections=[ReportSection(title="Intro", content="Body", citation_ids=["id-1"])],
        citations=[_citation("id-1")],
    )
    assert len(report.citations) == 1
    assert isinstance(report.generated_at, datetime)


def test_at_least_one_citation_required() -> None:
    with pytest.raises(InvalidDomainValue):
        Report(query_id=uuid4(), sections=[], citations=[])


def test_empty_citation_collection_rejected() -> None:
    section = ReportSection(title="Intro", content="Body")
    with pytest.raises(InvalidDomainValue):
        Report(query_id=uuid4(), sections=[section], citations=[])


def test_report_with_no_sections_but_a_citation_is_valid() -> None:
    # The hard invariant is >= 1 citation; sections may be empty.
    report = Report(query_id=uuid4(), sections=[], citations=[_citation()])
    assert report.sections == ()


def test_non_uuid_query_id_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Report(query_id="nope", sections=[], citations=[_citation()])  # type: ignore[arg-type]


def test_non_datetime_generated_at_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Report(
            query_id=uuid4(),
            sections=[],
            citations=[_citation()],
            generated_at="now",  # type: ignore[arg-type]
        )


def test_sequences_are_normalised_to_tuples() -> None:
    report = Report(
        query_id=uuid4(),
        sections=[ReportSection(title="A", content="B")],
        citations=[_citation()],
    )
    assert isinstance(report.sections, tuple)
    assert isinstance(report.citations, tuple)


def test_section_referencing_unknown_citation_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Report(
            query_id=uuid4(),
            sections=[ReportSection(title="A", content="B", citation_ids=["missing"])],
            citations=[_citation("id-1")],
        )


def test_section_referencing_known_citation_accepted() -> None:
    report = Report(
        query_id=uuid4(),
        sections=[ReportSection(title="A", content="B", citation_ids=["id-1"])],
        citations=[_citation("id-1")],
    )
    assert report.sections[0].citation_ids == ("id-1",)


def test_non_citation_in_citations_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Report(query_id=uuid4(), sections=[], citations=["not-a-citation"])  # type: ignore[list-item]


def test_non_section_in_sections_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Report(query_id=uuid4(), sections=["nope"], citations=[_citation()])  # type: ignore[list-item]


def test_is_immutable() -> None:
    report = Report(query_id=uuid4(), sections=[], citations=[_citation()])
    with pytest.raises(Exception):
        report.citations = ()  # type: ignore[misc]


# --- ReportSection -------------------------------------------------------


def test_section_valid_construction() -> None:
    section = ReportSection(title="Findings", content="Details", citation_ids=["id-1"])
    assert section.title == "Findings"
    assert section.citation_ids == ("id-1",)


def test_section_default_has_no_citations() -> None:
    section = ReportSection(title="Findings", content="Details")
    assert section.citation_ids == ()


def test_section_empty_title_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        ReportSection(title="", content="Details")


def test_section_whitespace_title_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        ReportSection(title="   ", content="Details")


def test_section_empty_content_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        ReportSection(title="Findings", content="")


def test_section_empty_citation_id_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        ReportSection(title="Findings", content="Details", citation_ids=[""])


def test_section_citation_ids_normalised_to_tuple() -> None:
    section = ReportSection(title="A", content="B", citation_ids=["x", "y"])
    assert section.citation_ids == ("x", "y")


def test_section_is_immutable() -> None:
    section = ReportSection(title="A", content="B")
    with pytest.raises(Exception):
        section.title = "Changed"  # type: ignore[misc]

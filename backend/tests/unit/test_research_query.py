"""Tests for the ResearchQuery entity and its invariants."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from domain.entities.research_query import ResearchQuery, ResearchStatus
from domain.exceptions import InvalidDomainValue


def test_valid_construction_populates_defaults() -> None:
    query = ResearchQuery(topic="How do heat pumps work?")
    assert query.topic == "How do heat pumps work?"
    assert isinstance(query.id, UUID)
    assert isinstance(query.created_at, datetime)
    assert query.status is ResearchStatus.PENDING


def test_explicit_fields_are_honoured() -> None:
    qid = uuid4()
    created = datetime(2026, 1, 1, tzinfo=timezone.utc)
    query = ResearchQuery(
        topic="Battery chemistry",
        id=qid,
        created_at=created,
        status=ResearchStatus.RUNNING,
    )
    assert query.id == qid
    assert query.created_at == created
    assert query.status is ResearchStatus.RUNNING


def test_empty_topic_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        ResearchQuery(topic="")


def test_whitespace_only_topic_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        ResearchQuery(topic="   \t\n ")


@pytest.mark.parametrize("status", list(ResearchStatus))
def test_all_valid_statuses_accepted(status: ResearchStatus) -> None:
    assert ResearchQuery(topic="x", status=status).status is status


def test_invalid_status_rejected() -> None:
    # A caller bypassing the type hint with a raw string must be rejected.
    with pytest.raises(InvalidDomainValue):
        ResearchQuery(topic="x", status="pending")  # type: ignore[arg-type]


def test_non_uuid_id_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        ResearchQuery(topic="x", id="not-a-uuid")  # type: ignore[arg-type]


def test_non_datetime_created_at_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        ResearchQuery(topic="x", created_at="2026-01-01")  # type: ignore[arg-type]


def test_status_enum_has_expected_members() -> None:
    assert {s.name for s in ResearchStatus} == {"PENDING", "RUNNING", "DONE", "FAILED"}


def test_is_immutable() -> None:
    query = ResearchQuery(topic="x")
    with pytest.raises(Exception):
        query.status = ResearchStatus.DONE  # type: ignore[misc]

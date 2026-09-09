"""Tests for the Citation entity and its provenance invariants."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from domain.entities.citation import Citation
from domain.exceptions import InvalidDomainValue


def _valid() -> Citation:
    return Citation(
        source_url_or_id="https://example.com/doc/1",
        source_name="Example Docs",
        retrieved_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )


def test_valid_construction() -> None:
    citation = _valid()
    assert citation.source_url_or_id == "https://example.com/doc/1"
    assert citation.source_name == "Example Docs"
    assert isinstance(citation.retrieved_at, datetime)


def test_empty_source_identifier_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Citation(
            source_url_or_id="",
            source_name="Example",
            retrieved_at=datetime.now(timezone.utc),
        )


def test_whitespace_source_identifier_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Citation(
            source_url_or_id="   ",
            source_name="Example",
            retrieved_at=datetime.now(timezone.utc),
        )


def test_empty_source_name_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Citation(
            source_url_or_id="id-1",
            source_name="",
            retrieved_at=datetime.now(timezone.utc),
        )


def test_whitespace_source_name_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Citation(
            source_url_or_id="id-1",
            source_name="  ",
            retrieved_at=datetime.now(timezone.utc),
        )


def test_non_datetime_retrieved_at_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Citation(
            source_url_or_id="id-1",
            source_name="Example",
            retrieved_at="2026-03-01",  # type: ignore[arg-type]
        )


def test_is_value_object_equality() -> None:
    assert _valid() == _valid()


def test_is_immutable() -> None:
    citation = _valid()
    with pytest.raises(Exception):
        citation.source_name = "Changed"  # type: ignore[misc]

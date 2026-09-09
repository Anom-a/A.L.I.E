"""Tests for the Evidence entity and its invariants."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from domain.entities.citation import Citation
from domain.entities.evidence import Evidence, SourceType
from domain.exceptions import InvalidDomainValue


def _citation() -> Citation:
    return Citation(
        source_url_or_id="id-1",
        source_name="Example",
        retrieved_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )


def _valid_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "sub_question_id": uuid4(),
        "source_type": SourceType.WEB,
        "content": "Heat pumps move heat rather than generate it.",
        "citation": _citation(),
    }
    base.update(overrides)
    return base


def test_valid_construction() -> None:
    evidence = Evidence(**_valid_kwargs())  # type: ignore[arg-type]
    assert evidence.content
    assert isinstance(evidence.id, UUID)
    assert isinstance(evidence.sub_question_id, UUID)
    assert evidence.source_type is SourceType.WEB
    assert isinstance(evidence.citation, Citation)


def test_empty_content_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Evidence(**_valid_kwargs(content=""))  # type: ignore[arg-type]


def test_whitespace_content_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Evidence(**_valid_kwargs(content="   \n"))  # type: ignore[arg-type]


def test_citation_required() -> None:
    with pytest.raises(InvalidDomainValue):
        Evidence(**_valid_kwargs(citation=None))  # type: ignore[arg-type]


def test_non_citation_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Evidence(**_valid_kwargs(citation="see source"))  # type: ignore[arg-type]


def test_non_uuid_sub_question_id_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Evidence(**_valid_kwargs(sub_question_id="nope"))  # type: ignore[arg-type]


def test_non_uuid_id_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Evidence(**_valid_kwargs(id="nope"))  # type: ignore[arg-type]


def test_invalid_source_type_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        Evidence(**_valid_kwargs(source_type="web"))  # type: ignore[arg-type]


@pytest.mark.parametrize("source_type", list(SourceType))
def test_every_source_type_accepted(source_type: SourceType) -> None:
    evidence = Evidence(**_valid_kwargs(source_type=source_type))  # type: ignore[arg-type]
    assert evidence.source_type is source_type

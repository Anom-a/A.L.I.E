"""Tests for the SubQuestion entity and its invariants."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from domain.entities.sub_question import SubQuestion, SubQuestionStatus
from domain.exceptions import InvalidDomainValue
from domain.value_objects.tool_category import ToolCategory


def _valid_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "research_query_id": uuid4(),
        "text": "What refrigerant does this model use?",
        "category": ToolCategory.REPAIR,
    }
    base.update(overrides)
    return base


def test_valid_construction_populates_defaults() -> None:
    sub = SubQuestion(**_valid_kwargs())  # type: ignore[arg-type]
    assert sub.text
    assert isinstance(sub.id, UUID)
    assert isinstance(sub.research_query_id, UUID)
    assert sub.category is ToolCategory.REPAIR
    assert sub.status is SubQuestionStatus.PENDING


def test_empty_text_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        SubQuestion(**_valid_kwargs(text=""))  # type: ignore[arg-type]


def test_whitespace_only_text_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        SubQuestion(**_valid_kwargs(text="   "))  # type: ignore[arg-type]


def test_invalid_category_rejected() -> None:
    # A raw string instead of a ToolCategory member must be rejected.
    with pytest.raises(InvalidDomainValue):
        SubQuestion(**_valid_kwargs(category="repair"))  # type: ignore[arg-type]


def test_non_uuid_research_query_id_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        SubQuestion(**_valid_kwargs(research_query_id="nope"))  # type: ignore[arg-type]


def test_non_uuid_id_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        SubQuestion(**_valid_kwargs(id="nope"))  # type: ignore[arg-type]


def test_invalid_status_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        SubQuestion(**_valid_kwargs(status="pending"))  # type: ignore[arg-type]


@pytest.mark.parametrize("category", list(ToolCategory))
def test_every_category_accepted(category: ToolCategory) -> None:
    assert SubQuestion(**_valid_kwargs(category=category)).category is category  # type: ignore[arg-type]


def test_status_enum_has_expected_members() -> None:
    assert {s.name for s in SubQuestionStatus} == {"PENDING", "ANSWERED", "FAILED"}

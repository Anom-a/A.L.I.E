"""Tests for the ToolCategory enum: presence and stability of members."""

from __future__ import annotations

from domain.value_objects.tool_category import ToolCategory


def test_all_four_members_exist() -> None:
    assert {member.name for member in ToolCategory} == {
        "REPAIR",
        "ACADEMIC",
        "NEWS",
        "GENERAL",
    }


def test_exactly_four_members() -> None:
    assert len(list(ToolCategory)) == 4


def test_member_values_are_stable_and_explicit() -> None:
    # Values are pinned so persistence/serialisation in later phases stays stable.
    assert ToolCategory.REPAIR.value == "repair"
    assert ToolCategory.ACADEMIC.value == "academic"
    assert ToolCategory.NEWS.value == "news"
    assert ToolCategory.GENERAL.value == "general"


def test_lookup_by_value() -> None:
    assert ToolCategory("news") is ToolCategory.NEWS


def test_members_are_distinct() -> None:
    values = [member.value for member in ToolCategory]
    assert len(values) == len(set(values))

"""Tests for the ToolCallAttempt entity and its invariants."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.entities.tool_call_attempt import ToolCallAttempt
from domain.exceptions import InvalidDomainValue


def test_valid_construction() -> None:
    attempt = ToolCallAttempt(
        tool_name="web_search",
        sub_question_id=uuid4(),
        succeeded=True,
    )
    assert attempt.tool_name == "web_search"
    assert attempt.succeeded is True
    assert attempt.fallback_used is False  # default
    assert isinstance(attempt.timestamp, datetime)


def test_empty_tool_name_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        ToolCallAttempt(tool_name="", sub_question_id=uuid4(), succeeded=True)


def test_whitespace_tool_name_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        ToolCallAttempt(tool_name="   ", sub_question_id=uuid4(), succeeded=True)


def test_successful_call_represented() -> None:
    attempt = ToolCallAttempt(
        tool_name="web_search", sub_question_id=uuid4(), succeeded=True
    )
    assert attempt.succeeded is True


def test_failed_call_represented() -> None:
    attempt = ToolCallAttempt(
        tool_name="web_search", sub_question_id=uuid4(), succeeded=False
    )
    assert attempt.succeeded is False


def test_fallback_flag_represented() -> None:
    attempt = ToolCallAttempt(
        tool_name="academic_search",
        sub_question_id=uuid4(),
        succeeded=True,
        fallback_used=True,
    )
    assert attempt.fallback_used is True


def test_explicit_timestamp_honoured() -> None:
    ts = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    attempt = ToolCallAttempt(
        tool_name="t", sub_question_id=uuid4(), succeeded=True, timestamp=ts
    )
    assert attempt.timestamp == ts


def test_non_uuid_sub_question_id_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        ToolCallAttempt(tool_name="t", sub_question_id="x", succeeded=True)  # type: ignore[arg-type]


@pytest.mark.parametrize("field", ["succeeded", "fallback_used"])
def test_non_bool_flags_rejected(field: str) -> None:
    kwargs: dict[str, object] = {
        "tool_name": "t",
        "sub_question_id": uuid4(),
        "succeeded": True,
    }
    kwargs[field] = "yes"
    with pytest.raises(InvalidDomainValue):
        ToolCallAttempt(**kwargs)  # type: ignore[arg-type]


def test_non_datetime_timestamp_rejected() -> None:
    with pytest.raises(InvalidDomainValue):
        ToolCallAttempt(
            tool_name="t",
            sub_question_id=uuid4(),
            succeeded=True,
            timestamp="today",  # type: ignore[arg-type]
        )

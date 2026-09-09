"""ToolCallAttempt: a record of one attempt to use one tool for one sub-question.

This is an audit/observability record, not a controller. It states *what
happened* — which tool ran, for which sub-question, whether it succeeded, and
whether a fallback was used — at a point in time. It deliberately contains no
retry logic, no scheduling, and no I/O; orchestration lives in a later phase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from domain.exceptions import InvalidDomainValue


@dataclass(frozen=True, slots=True)
class ToolCallAttempt:
    """An immutable record of a single tool invocation attempt."""

    tool_name: str
    sub_question_id: UUID
    succeeded: bool
    fallback_used: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.tool_name or not self.tool_name.strip():
            raise InvalidDomainValue("ToolCallAttempt tool_name must not be empty")
        if not isinstance(self.sub_question_id, UUID):
            raise InvalidDomainValue("ToolCallAttempt sub_question_id must be a UUID")
        if not isinstance(self.succeeded, bool):
            raise InvalidDomainValue("ToolCallAttempt succeeded must be a bool")
        if not isinstance(self.fallback_used, bool):
            raise InvalidDomainValue("ToolCallAttempt fallback_used must be a bool")
        if not isinstance(self.timestamp, datetime):
            raise InvalidDomainValue("ToolCallAttempt timestamp must be a datetime")

"""SubQuestion: one decomposed research question.

A research query is broken down into several focused sub-questions. Each one
carries a :class:`ToolCategory` that a later routing layer will use to decide
how to research it, plus its own lifecycle status. The category is stored, not
computed — classification is an outer-layer concern in a future phase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

from domain.exceptions import InvalidDomainValue
from domain.value_objects.tool_category import ToolCategory


class SubQuestionStatus(Enum):
    """Lifecycle status of a single sub-question."""

    PENDING = "pending"
    ANSWERED = "answered"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class SubQuestion:
    """One focused question decomposed from a research query."""

    research_query_id: UUID
    text: str
    category: ToolCategory
    id: UUID = field(default_factory=uuid4)
    status: SubQuestionStatus = SubQuestionStatus.PENDING

    def __post_init__(self) -> None:
        if not isinstance(self.research_query_id, UUID):
            raise InvalidDomainValue("SubQuestion research_query_id must be a UUID")
        if not self.text or not self.text.strip():
            raise InvalidDomainValue("SubQuestion text must not be empty")
        if not isinstance(self.category, ToolCategory):
            raise InvalidDomainValue(
                "SubQuestion category must be a ToolCategory member"
            )
        if not isinstance(self.id, UUID):
            raise InvalidDomainValue("SubQuestion id must be a UUID")
        if not isinstance(self.status, SubQuestionStatus):
            raise InvalidDomainValue(
                "SubQuestion status must be a SubQuestionStatus member"
            )

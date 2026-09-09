"""ToolCategory: the high-level research category for a sub-question.

This value object is deliberately behaviour-free. It classifies a
sub-question so that a *later* routing layer can decide which concrete tool or
gateway to use. It must not contain routing logic or any mapping to gateways
— that belongs in an outer layer in a future phase.
"""

from __future__ import annotations

from enum import Enum


class ToolCategory(Enum):
    """High-level category used later to route research to the right tool."""

    REPAIR = "repair"
    ACADEMIC = "academic"
    NEWS = "news"
    GENERAL = "general"

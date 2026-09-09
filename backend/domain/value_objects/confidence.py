"""Confidence: a bounded [0.0, 1.0] confidence score.

Modelled as an immutable value object so it can be safely shared and compared.
It will be used later to express confidence in evidence and in critique, but it
carries no I/O, no framework dependency, and no external validation library —
just the domain invariant that a confidence lies within the unit interval.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.exceptions import InvalidDomainValue

MIN_CONFIDENCE: float = 0.0
MAX_CONFIDENCE: float = 1.0


@dataclass(frozen=True, slots=True)
class Confidence:
    """A confidence score constrained to the closed interval [0.0, 1.0]."""

    value: float

    def __post_init__(self) -> None:
        # Reject bools explicitly: bool is a subclass of int and would silently
        # pass the numeric check (True == 1.0, False == 0.0), which is not a
        # meaningful confidence value.
        if isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise InvalidDomainValue(
                f"Confidence must be a real number, got {type(self.value).__name__}"
            )
        if not MIN_CONFIDENCE <= float(self.value) <= MAX_CONFIDENCE:
            raise InvalidDomainValue(
                f"Confidence must be within [{MIN_CONFIDENCE}, {MAX_CONFIDENCE}], "
                f"got {self.value}"
            )

    @classmethod
    def minimum(cls) -> "Confidence":
        """Lowest possible confidence."""
        return cls(MIN_CONFIDENCE)

    @classmethod
    def maximum(cls) -> "Confidence":
        """Highest possible confidence."""
        return cls(MAX_CONFIDENCE)

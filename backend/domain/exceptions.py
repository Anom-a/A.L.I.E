"""Domain-level exceptions.

Kept intentionally minimal. Domain entities and value objects raise these
instead of leaking generic or framework-specific validation errors, so callers
in outer layers can distinguish invalid-domain-input from other failures.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain errors."""


class InvalidDomainValue(DomainError):
    """Raised when an entity or value object violates a domain invariant."""

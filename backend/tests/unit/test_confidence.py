"""Tests for the Confidence value object and its range invariant."""

from __future__ import annotations

import pytest

from domain.exceptions import DomainError, InvalidDomainValue
from domain.value_objects.confidence import (
    MAX_CONFIDENCE,
    MIN_CONFIDENCE,
    Confidence,
)


def test_minimum_value_accepted() -> None:
    assert Confidence(0.0).value == 0.0


def test_maximum_value_accepted() -> None:
    assert Confidence(1.0).value == 1.0


@pytest.mark.parametrize("value", [0.01, 0.25, 0.5, 0.75, 0.999])
def test_normal_values_accepted(value: float) -> None:
    assert Confidence(value).value == value


def test_integer_bounds_accepted() -> None:
    # ints within range are valid real numbers
    assert Confidence(0).value == 0
    assert Confidence(1).value == 1


@pytest.mark.parametrize("value", [-0.0001, -1.0, -100.0])
def test_below_minimum_rejected(value: float) -> None:
    with pytest.raises(InvalidDomainValue):
        Confidence(value)


@pytest.mark.parametrize("value", [1.0001, 2.0, 100.0])
def test_above_maximum_rejected(value: float) -> None:
    with pytest.raises(InvalidDomainValue):
        Confidence(value)


def test_invalid_domain_value_is_a_domain_error() -> None:
    # Outer layers can catch the broad DomainError base.
    with pytest.raises(DomainError):
        Confidence(5.0)


@pytest.mark.parametrize("value", [True, False])
def test_bool_rejected(value: bool) -> None:
    # bool is an int subclass; it must not masquerade as a confidence score.
    with pytest.raises(InvalidDomainValue):
        Confidence(value)


@pytest.mark.parametrize("value", ["0.5", None, object()])
def test_non_numeric_rejected(value: object) -> None:
    with pytest.raises(InvalidDomainValue):
        Confidence(value)  # type: ignore[arg-type]


def test_bounds_constants() -> None:
    assert MIN_CONFIDENCE == 0.0
    assert MAX_CONFIDENCE == 1.0


def test_factory_helpers() -> None:
    assert Confidence.minimum() == Confidence(0.0)
    assert Confidence.maximum() == Confidence(1.0)


def test_is_immutable() -> None:
    c = Confidence(0.5)
    with pytest.raises(Exception):
        c.value = 0.9  # type: ignore[misc]


def test_value_equality() -> None:
    assert Confidence(0.4) == Confidence(0.4)
    assert Confidence(0.4) != Confidence(0.6)

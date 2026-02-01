"""Tests for calculator operations.

These tests serve as evidence tests for the calculator functionality intention.
"""

from src.calculator.operations import add, subtract


def test_add_positive():
    """Test adding positive numbers."""
    assert add(2, 3) == 5


def test_add_negative():
    """Test adding negative numbers."""
    assert add(-1, -1) == -2


def test_add_zero():
    """Test adding zero."""
    assert add(5, 0) == 5


def test_subtract_positive():
    """Test subtracting positive numbers."""
    assert subtract(5, 3) == 2


def test_subtract_negative():
    """Test subtracting negative numbers."""
    assert subtract(-1, -1) == 0

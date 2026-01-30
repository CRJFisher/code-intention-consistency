"""Tests for calculator module - evidence tests for intention audit."""

from src.feature_x.calculator import add


def test_add_positive_numbers():
    """Evidence test: add function works with positive numbers."""
    assert add(2, 3) == 5


def test_add_negative_numbers():
    """Evidence test: add function works with negative numbers."""
    assert add(-1, -1) == -2


def test_add_zero():
    """Evidence test: add function handles zero correctly."""
    assert add(0, 5) == 5
    assert add(5, 0) == 5

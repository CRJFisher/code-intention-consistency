"""Tests for payment processor."""

from src.payments.processor import process_payment, validate_amount


def test_process_payment():
    result = process_payment(100.0)
    assert result["status"] == "success"
    assert result["amount"] == 100.0


def test_validate_amount_positive():
    assert validate_amount(50.0) is True


def test_validate_amount_negative():
    assert validate_amount(-10.0) is False

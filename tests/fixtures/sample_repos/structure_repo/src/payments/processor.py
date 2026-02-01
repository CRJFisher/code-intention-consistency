"""Payment processing module."""


def process_payment(amount: float, currency: str = "USD") -> dict:
    """Process a payment transaction."""
    return {
        "status": "success",
        "amount": amount,
        "currency": currency,
        "transaction_id": "TXN-001",
    }


def validate_amount(amount: float) -> bool:
    """Validate payment amount is positive."""
    return amount > 0

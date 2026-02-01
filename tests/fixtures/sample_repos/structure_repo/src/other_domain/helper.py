"""Helper utilities that SHOULD be in payments domain."""


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format amount with currency symbol."""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£"}
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:.2f}"

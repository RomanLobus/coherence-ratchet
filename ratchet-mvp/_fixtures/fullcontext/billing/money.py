"""Canonical money helpers. Currency conversion lives here and only here."""
from decimal import Decimal, ROUND_HALF_UP


def to_cents(amount) -> int:
    """Convert a decimal currency amount to integer cents (commercial rounding)."""
    return int((Decimal(str(amount)) * 100).to_integral_value(rounding=ROUND_HALF_UP))

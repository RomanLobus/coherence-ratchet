"""Fixtures reproducing silent behaviour changes from the experiments — cases a porous
characterisation suite misses and the bounded comparison must expose.

  - to_cents_half_up / to_cents_half_even: the integrator's silent HALF_UP -> HALF_EVEN rounding flip.
  - retry_orig / retry_canon: two divergences at once — a 4->3 try-count and catching Exception
    instead of only TransientError (retrying a ValueError that should propagate).
  - retry_faithful: a matching consolidation within the explicit retry strategy.
"""
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP


def to_cents_half_up(amount: float) -> int:
    """Original: commercial rounding (half rounds up)."""
    return int(Decimal(str(amount)).scaleb(2).to_integral_value(rounding=ROUND_HALF_UP))


def to_cents_half_even(amount: float) -> int:
    """Canonical the integrator produced: banker's rounding — a silent change at the half-cent."""
    return int(Decimal(str(amount)).scaleb(2).to_integral_value(rounding=ROUND_HALF_EVEN))


class TransientError(Exception):
    pass


def retry_orig(op, attempts: int = 4):
    """Original: up to 4 tries, retries ONLY TransientError (a ValueError propagates immediately)."""
    err = None
    for _ in range(attempts):
        try:
            return op()
        except TransientError as e:
            err = e
    raise err


def retry_canon(op, attempts: int = 3):
    """Canonical a naive merge produced: 3 tries, catches Exception — two silent behaviour changes."""
    err = None
    for _ in range(attempts):
        try:
            return op()
        except Exception as e:
            err = e
    raise err


def retry_faithful(op, attempts: int = 4):
    """A faithful consolidation of retry_orig: same try-count, same exception selectivity."""
    err = None
    for _ in range(attempts):
        try:
            return op()
        except TransientError as e:
            err = e
    raise err

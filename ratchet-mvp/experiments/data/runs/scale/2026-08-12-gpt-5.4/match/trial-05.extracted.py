"""Order total helpers."""

from .money import to_cents


def order_total(order):
    """Return the total order value as an integer number of cents."""
    return sum(line["qty"] * to_cents(line["price"]) for line in order["lines"])

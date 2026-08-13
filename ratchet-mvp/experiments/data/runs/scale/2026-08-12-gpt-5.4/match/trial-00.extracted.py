"""Order total helpers."""

from .money import to_cents


def order_total(order):
    """Return the total order value as an integer number of cents."""
    total = 0
    for line in order.get('lines', []):
        total += line['qty'] * to_cents(line['price'])
    return total

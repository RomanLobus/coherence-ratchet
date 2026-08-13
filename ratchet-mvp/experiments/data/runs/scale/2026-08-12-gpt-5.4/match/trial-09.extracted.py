"""Order total helpers."""

from .money import to_cents


def order_total(order):
    """Return the total order value as an integer number of cents."""
    total_cents = 0
    for line in order['lines']:
        total_cents += line['qty'] * to_cents(line['price'])
    return total_cents

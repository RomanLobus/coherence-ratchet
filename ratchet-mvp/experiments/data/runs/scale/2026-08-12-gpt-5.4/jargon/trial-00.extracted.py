"""Order total calculation."""

from .settle import to_minor_units


def order_total(order):
    """Return the total order value as an integer number of cents."""
    total = 0
    for line in order.get('lines', []):
        total += int(line['qty']) * to_minor_units(line['price'])
    return total

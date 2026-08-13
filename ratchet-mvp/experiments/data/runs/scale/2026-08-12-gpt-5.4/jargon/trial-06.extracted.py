"""Order total calculation."""

from decimal import Decimal

from .settle import to_minor_units


def order_total(order):
    """Return the total order value as an integer number of cents."""
    total = Decimal("0")

    for line in order["lines"]:
        total += Decimal(str(line["qty"])) * Decimal(str(line["price"]))

    return to_minor_units(total)

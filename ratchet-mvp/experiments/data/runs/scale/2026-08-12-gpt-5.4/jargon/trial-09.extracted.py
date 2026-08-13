"""Order total calculation."""
from decimal import Decimal

from .settle import to_minor_units


def order_total(order):
    """Return the total order value in cents for the given order."""
    total = Decimal("0")
    for line in order["lines"]:
        total += Decimal(str(line["price"])) * line["qty"]
    return to_minor_units(total)

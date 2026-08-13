"""Order total calculation."""

from shop.settle import to_minor_units


def order_total(order):
    """Return the total order value in cents for the given order."""
    return sum(line["qty"] * to_minor_units(line["price"]) for line in order["lines"])

"""Order total helpers."""

from shop.money import to_cents


def order_total(order):
    """Return the order total as an integer number of cents."""
    return sum(line["qty"] * to_cents(line["price"]) for line in order["lines"])

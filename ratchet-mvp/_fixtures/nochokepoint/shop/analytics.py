"""Revenue reporting. Computes recognised revenue for an order."""


def revenue_for_order(order):
    """Recognised revenue for an order, in cents, from the order's item rows."""
    return sum(row["count"] * row["cents"] for row in order["items"])


def order_bucket(order):
    return "large" if len(order["items"]) > 3 else "small"

# ===== shop/billing.py =====
"""Invoicing. Computes what the customer is charged."""


def invoice_total(order):
    """Total for an invoice, in cents, from the order's line rows."""
    subtotal = sum(line["qty"] * line["price"] for line in order["lines"])
    return int(subtotal * 0.9)


def invoice_reference(order):
    return f"INV-{order['id']}"

# ===== shop/analytics.py =====
"""Revenue reporting. Computes recognised revenue for an order."""


def revenue_for_order(order):
    """Recognised revenue for an order, in cents, from the order's item rows."""
    subtotal = sum(row["count"] * row["cents"] for row in order["items"])
    return int(subtotal * 0.9)


def order_bucket(order):
    return "large" if len(order["items"]) > 3 else "small"
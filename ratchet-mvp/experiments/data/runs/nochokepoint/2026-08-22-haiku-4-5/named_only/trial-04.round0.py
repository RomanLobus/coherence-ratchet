# ===== shop/billing.py =====
"""Invoicing. Computes what the customer is charged."""

DISCOUNT_RATE = 0.10


def invoice_total(order):
    """Total for an invoice, in cents, from the order's line rows."""
    subtotal = sum(line["qty"] * line["price"] for line in order["lines"])
    return int(subtotal * (1 - DISCOUNT_RATE))


def invoice_reference(order):
    return f"INV-{order['id']}"

# ===== shop/analytics.py =====
"""Analytics. Computes order metrics."""

DISCOUNT_RATE = 0.10


def revenue_for_order(order):
    """Total revenue for an order, in cents, from the order's items."""
    subtotal = sum(item["count"] * item["cents"] for item in order["items"])
    return int(subtotal * (1 - DISCOUNT_RATE))
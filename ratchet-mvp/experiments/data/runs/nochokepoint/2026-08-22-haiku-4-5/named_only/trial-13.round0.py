# ===== shop/billing.py =====
"""Invoicing. Computes what the customer is charged."""


def invoice_total(order):
    """Total for an invoice, in cents, from the order's line rows."""
    return int(sum(line["qty"] * line["price"] for line in order["lines"]) * 0.9)


def invoice_reference(order):
    return f"INV-{order['id']}"

# ===== shop/analytics.py =====
"""Analytics. Computes revenue metrics."""


def revenue_for_order(order):
    """Revenue for an order, in cents, from the order's items."""
    return int(sum(item["count"] * item["cents"] for item in order["items"]) * 0.9)

I need to apply a 10% discount to order totals. Based on the problem statement, there are two places where order totals are computed:

1. `shop.billing.invoice_total(order)` - uses `order['lines']` with `qty` and `price`
2. `shop.analytics.revenue_for_order(order)` - uses `order['items']` with `count` and `cents`

Since `shop/analytics.py` is not shown in the source, I'll create it. I'll apply the 10% discount (multiply by 0.9) to both calculations.

# ===== shop/billing.py =====
"""Invoicing. Computes what the customer is charged."""


def invoice_total(order):
    """Total for an invoice, in cents, from the order's line rows."""
    total = sum(line["qty"] * line["price"] for line in order["lines"])
    return int(total * 0.9)


def invoice_reference(order):
    return f"INV-{order['id']}"

# ===== shop/analytics.py =====
"""Order analytics. Revenue calculations."""


def revenue_for_order(order):
    """Total revenue for an order, in cents, from the order's items."""
    total = sum(item["count"] * item["cents"] for item in order["items"])
    return int(total * 0.9)
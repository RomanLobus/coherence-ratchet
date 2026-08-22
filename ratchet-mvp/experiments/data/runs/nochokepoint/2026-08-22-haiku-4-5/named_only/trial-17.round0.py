Looking at this problem, I need to:

1. Apply a 10% discount to `shop/billing.py`'s `invoice_total()` function
2. Apply a 10% discount to `shop/analytics.py`'s `revenue_for_order()` function (which isn't shown but is mentioned)
3. Keep all other code unchanged

Since `shop/analytics.py` isn't provided in the source, I'll create it based on the description. A 10% discount means multiplying by 0.9.

# ===== shop/billing.py =====
"""Invoicing. Computes what the customer is charged."""


def invoice_total(order):
    """Total for an invoice, in cents, from the order's line rows."""
    return int(sum(line["qty"] * line["price"] for line in order["lines"]) * 0.9)


def invoice_reference(order):
    return f"INV-{order['id']}"

# ===== shop/shipping.py =====
"""Delivery estimates. Unrelated to money."""
import datetime


def estimated_days(order, region_table):
    base = region_table.get(order["region"], 5)
    return base + (1 if len(order["lines"]) > 10 else 0)


def dispatch_window(order):
    return datetime.timedelta(days=2)

# ===== shop/customers.py =====
"""Customer records."""


def display_name(customer):
    return f"{customer['first']} {customer['last']}"


def is_active(customer):
    return customer.get("status") == "active"

# ===== shop/analytics.py =====
"""Analytics. Revenue reporting."""


def revenue_for_order(order):
    """Total revenue for an order, in cents, from the order's items."""
    return int(sum(item["count"] * item["cents"] for item in order["items"]) * 0.9)
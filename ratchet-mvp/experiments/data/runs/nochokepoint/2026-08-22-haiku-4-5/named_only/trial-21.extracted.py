# ===== shop/billing.py =====
"""Invoicing. Computes what the customer is charged."""


def invoice_total(order):
    """Total for an invoice, in cents, from the order's line rows."""
    total = sum(line["qty"] * line["price"] for line in order["lines"])
    return int(total * 0.9)


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
    total = sum(item["count"] * item["cents"] for item in order["items"])
    return int(total * 0.9)
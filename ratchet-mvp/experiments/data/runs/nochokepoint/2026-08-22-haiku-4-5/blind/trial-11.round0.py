# ===== shop/billing.py =====
"""Invoicing. Computes what the customer is charged."""


def invoice_total(order):
    """Total for an invoice, in cents, from the order's line rows."""
    subtotal = sum(line["qty"] * line["price"] for line in order["lines"])
    return int(subtotal * 0.9)


def invoice_reference(order):
    return f"INV-{order['id']}"
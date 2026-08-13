# ===== billing/charges.py =====
"""Customer charging — charges submitted to payment gateway with automatic retry."""
from billing.money import to_cents
from billing.retry import retry


def charge_customer(order, gateway):
    """Convert order amount to cents and submit charge to gateway, retrying on transient failure."""
    amount_cents = to_cents(order["amount"])
    return retry(lambda: gateway.submit(order["id"], amount_cents))

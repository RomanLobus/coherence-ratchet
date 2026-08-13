# ===== billing/charges.py =====
"""Customer charging — orchestrates money conversion and retry logic."""
from billing.money import to_cents
from billing.retry import retry


def charge_customer(order, gateway):
    """Convert order amount to cents and submit charge via gateway, retrying on failure."""
    amount_cents = to_cents(order["amount"])
    return retry(lambda: gateway.submit(order["id"], amount_cents))

"""Charges."""
from billing.internal.num import _q
from billing.internal.exec import _attempt


def charge_customer(order, gateway):
    """Convert order amount to cents and submit charge with retry logic."""
    amount_cents = _q(order['amount'])
    return _attempt(lambda: gateway.submit(order['id'], amount_cents))

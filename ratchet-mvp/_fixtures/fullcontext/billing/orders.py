"""Order submission — the existing sanctioned usage of the canonical helpers."""
from billing.money import to_cents
from billing.retry import retry


def submit_order(order, gateway):
    amount_cents = to_cents(order["amount"])
    return retry(lambda: gateway.submit(order["id"], amount_cents))

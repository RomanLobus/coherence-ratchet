"""Customer charge submission using the package's canonical helpers."""

from billing.money import to_cents
from billing.retry import retry


def charge_customer(order, gateway):
    amount_cents = to_cents(order["amount"])
    return retry(lambda: gateway.submit(order["id"], amount_cents))

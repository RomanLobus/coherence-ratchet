from billing.money import to_cents
from billing.retry import retry


def charge_customer(order, gateway):
    amount_cents = to_cents(order["amount"])
    return retry(gateway.submit, order["id"], amount_cents, attempts=3, delay=0.5)

from billing.money import to_cents
from billing.retry import retry


def charge_customer(order, gateway):
    amount_cents = to_cents(order["amount"])
    submit = retry(gateway.submit)
    return submit(order["id"], amount_cents)

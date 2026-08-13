from billing.money import to_cents
from billing.retry import retry


def charge_customer(order, gateway):
    order_id = order["id"]
    amount_cents = to_cents(order["amount"])
    return retry(lambda: gateway.submit(order_id, amount_cents))

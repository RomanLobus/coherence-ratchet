from billing.money import to_cents
from billing.retry import retry


def charge_customer(order, gateway):
    amount_cents = to_cents(order["amount"])
    order_id = order["id"]

    def _submit():
        return gateway.submit(order_id, amount_cents)

    return retry(_submit)

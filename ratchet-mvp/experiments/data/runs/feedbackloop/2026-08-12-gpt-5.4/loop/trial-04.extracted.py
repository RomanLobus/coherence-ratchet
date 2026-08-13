from billing.money import to_cents
from billing.retry import retry


class ChargeError(Exception):
    """Raised when a charge cannot be completed."""


def charge_customer(order, gateway):
    order_id = order["id"]

    try:
        amount_cents = to_cents(order["amount"])
    except Exception as exc:
        raise ChargeError("Invalid order amount") from exc

    try:
        return retry(lambda: gateway.submit(order_id, amount_cents))
    except Exception as exc:
        raise ChargeError("Charge failed") from exc

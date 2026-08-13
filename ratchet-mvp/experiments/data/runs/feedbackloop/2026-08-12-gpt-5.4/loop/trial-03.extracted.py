from billing.money import to_cents
from billing.retry import retry


class ChargeError(Exception):
    """Raised when a customer charge cannot be completed."""


def charge_customer(order, gateway):
    order_id = order["id"]

    try:
        amount_cents = to_cents(order["amount"])
    except Exception as exc:
        raise ChargeError(f"Invalid order amount for order {order_id}: {order.get('amount')!r}") from exc

    try:
        return retry(lambda: gateway.submit(order_id, amount_cents))
    except Exception as exc:
        raise ChargeError(f"Failed to charge order {order_id}") from exc

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import time


class ChargeError(Exception):
    """Raised when a customer charge cannot be completed."""


def _to_cents(amount):
    try:
        decimal_amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ChargeError(f"Invalid order amount: {amount!r}") from exc

    cents = (decimal_amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def charge_customer(order, gateway):
    order_id = order["id"]
    amount_cents = _to_cents(order["amount"])

    attempts = 3
    delay_seconds = 0.1

    for attempt in range(1, attempts + 1):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            if attempt == attempts:
                raise ChargeError(f"Failed to charge order {order_id}") from exc
            time.sleep(delay_seconds)

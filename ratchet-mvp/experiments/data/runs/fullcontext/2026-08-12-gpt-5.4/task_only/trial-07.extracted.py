from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import time


class TransientChargeError(Exception):
    """Raised when a charge cannot be completed after transient failures."""


def _to_cents(amount):
    value = Decimal(str(amount))
    cents = (value * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def charge_customer(order, gateway):
    order_id = order["id"]

    try:
        amount_cents = _to_cents(order["amount"])
    except (KeyError, InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Invalid order amount") from exc

    max_attempts = 3
    delay_seconds = 0.1

    last_exc = None
    for attempt in range(max_attempts):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            if attempt == max_attempts - 1:
                last_exc = exc
                break
            time.sleep(delay_seconds)

    raise TransientChargeError("Charge failed after retries") from last_exc

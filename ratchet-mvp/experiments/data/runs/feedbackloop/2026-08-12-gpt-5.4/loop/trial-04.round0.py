from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import time


class ChargeError(Exception):
    """Raised when a charge cannot be completed."""


def _amount_to_cents(amount):
    try:
        cents = (Decimal(str(amount)) * Decimal("100")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ChargeError("Invalid order amount") from exc

    return int(cents)


def charge_customer(order, gateway):
    order_id = order["id"]
    amount_cents = _amount_to_cents(order["amount"])

    delays = (0.0, 0.1, 0.2)
    last_exc = None

    for attempt, delay in enumerate(delays, start=1):
        if delay:
            time.sleep(delay)
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            last_exc = exc
            is_transient = getattr(exc, "transient", False)
            if attempt == len(delays) or not is_transient:
                raise

    raise ChargeError("Charge failed") from last_exc

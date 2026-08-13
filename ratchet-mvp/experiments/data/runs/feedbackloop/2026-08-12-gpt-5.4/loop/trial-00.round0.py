from decimal import Decimal, ROUND_HALF_UP
import time


class TransientChargeError(Exception):
    """Raised when a charge cannot be completed after transient failures."""


def _to_cents(amount):
    cents = (Decimal(str(amount)) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def charge_customer(order, gateway):
    order_id = order["id"]
    amount_cents = _to_cents(order["amount"])

    delays = (0, 0.5, 1.0, 2.0)
    last_exc = None

    for attempt, delay in enumerate(delays, start=1):
        if delay:
            time.sleep(delay)
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            last_exc = exc
            is_transient = getattr(exc, "transient", False) or exc.__class__.__name__ in {
                "TimeoutError",
                "ConnectionError",
                "TemporaryError",
                "TransientError",
            }
            if attempt == len(delays) or not is_transient:
                raise

    raise TransientChargeError(f"Failed to charge order {order_id}") from last_exc

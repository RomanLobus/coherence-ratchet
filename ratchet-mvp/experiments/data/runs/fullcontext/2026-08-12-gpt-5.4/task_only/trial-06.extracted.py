from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import time


class TransientChargeError(Exception):
    """Raised when a charge cannot be completed after transient failures."""


def _to_cents(amount):
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid order amount: {amount!r}") from exc
    return int((value * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _is_transient_error(exc):
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    return getattr(exc, "transient", False) is True


def charge_customer(order, gateway):
    order_id = order["id"]
    amount_cents = _to_cents(order["amount"])

    last_exc = None
    for attempt in range(3):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            if not _is_transient_error(exc) or attempt == 2:
                if _is_transient_error(exc):
                    raise TransientChargeError(
                        f"Failed to charge order {order_id} after retries"
                    ) from exc
                raise
            last_exc = exc
            time.sleep(0.1 * (2 ** attempt))

    raise TransientChargeError(
        f"Failed to charge order {order_id} after retries"
    ) from last_exc

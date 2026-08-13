from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import time


class TransientChargeError(Exception):
    """Raised when a transient gateway failure persists after retries."""


def _to_cents(amount):
    try:
        cents = (Decimal(str(amount)) * Decimal("100")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid order amount: {amount!r}") from exc
    return int(cents)


def _is_transient_error(exc):
    if hasattr(exc, "transient"):
        return bool(exc.transient)
    return isinstance(exc, (TimeoutError, ConnectionError))


def charge_customer(order, gateway):
    amount_cents = _to_cents(order["amount"])
    order_id = order["id"]

    delays = (0.1, 0.2, 0.4)
    attempts = len(delays) + 1
    last_exc = None

    for attempt in range(attempts):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            if not _is_transient_error(exc):
                raise
            last_exc = exc
            if attempt == attempts - 1:
                break
            time.sleep(delays[attempt])

    raise TransientChargeError(
        f"Failed to charge order {order_id!r} after {attempts} attempts"
    ) from last_exc

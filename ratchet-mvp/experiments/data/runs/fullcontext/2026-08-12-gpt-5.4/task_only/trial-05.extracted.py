from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import time


_TRANSIENT_ERROR_NAMES = {
    "TimeoutError",
    "ConnectionError",
    "TemporaryError",
    "TransientError",
}


def _to_cents(amount):
    try:
        cents = (Decimal(str(amount)) * Decimal("100")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid order amount: {amount!r}") from exc
    return int(cents)


def _is_transient_error(exc):
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    return exc.__class__.__name__ in _TRANSIENT_ERROR_NAMES


def charge_customer(order, gateway):
    order_id = order["id"]
    amount_cents = _to_cents(order["amount"])

    delays = (0.1, 0.2, 0.4)
    attempts = len(delays) + 1

    last_exc = None
    for attempt in range(attempts):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            if not _is_transient_error(exc) or attempt == attempts - 1:
                raise
            last_exc = exc
            time.sleep(delays[attempt])

    raise last_exc

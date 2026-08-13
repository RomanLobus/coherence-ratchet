from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import time


_MAX_RETRIES = 3
_RETRYABLE_EXCEPTIONS = (TimeoutError, ConnectionError)
_RETRY_DELAYS_SECONDS = (0.1, 0.2, 0.4)


def _to_cents(amount):
    try:
        decimal_amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid order amount") from exc

    cents = (decimal_amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def charge_customer(order, gateway):
    amount_cents = _to_cents(order["amount"])
    order_id = order["id"]

    last_exc = None
    for attempt in range(_MAX_RETRIES):
        try:
            return gateway.submit(order_id, amount_cents)
        except _RETRYABLE_EXCEPTIONS as exc:
            last_exc = exc
            if attempt == _MAX_RETRIES - 1:
                break
            time.sleep(_RETRY_DELAYS_SECONDS[attempt])

    raise last_exc

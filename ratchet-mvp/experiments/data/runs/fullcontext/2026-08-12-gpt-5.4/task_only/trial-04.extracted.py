from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import time


MAX_RETRIES = 3
RETRY_EXCEPTIONS = ("temporary", "transient", "timeout", "connection")


def _to_cents(amount):
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid order amount") from exc
    return int((value * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _is_transient_error(exc):
    message = str(exc).lower()
    return any(token in message for token in RETRY_EXCEPTIONS)


def charge_customer(order, gateway):
    amount_cents = _to_cents(order["amount"])
    order_id = order["id"]

    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            if not _is_transient_error(exc) or attempt == MAX_RETRIES - 1:
                raise
            last_exc = exc
            time.sleep(0.1 * (attempt + 1))

    raise last_exc

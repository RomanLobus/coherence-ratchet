from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import time


_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 0.1


def _to_cents(amount):
    try:
        cents = (Decimal(str(amount)) * Decimal("100")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid order amount: {amount!r}") from exc
    return int(cents)


def charge_customer(order, gateway):
    amount_cents = _to_cents(order["amount"])
    order_id = order["id"]

    last_exc = None
    for attempt in range(_MAX_RETRIES):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            transient = getattr(exc, "transient", False)
            if not transient or attempt == _MAX_RETRIES - 1:
                raise
            last_exc = exc
            time.sleep(_RETRY_DELAY_SECONDS)

    raise last_exc

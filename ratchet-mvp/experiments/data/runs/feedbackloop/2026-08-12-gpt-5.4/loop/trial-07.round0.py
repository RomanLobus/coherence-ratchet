from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import time


_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 0.5


def _to_cents(amount):
    try:
        decimal_amount = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("order['amount'] must be a valid numeric value")

    cents = (decimal_amount * Decimal("100")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(cents)


def charge_customer(order, gateway):
    amount_cents = _to_cents(order["amount"])
    order_id = order["id"]

    last_error = None
    for attempt in range(_MAX_RETRIES):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            transient = getattr(exc, "transient", False)
            if not transient or attempt == _MAX_RETRIES - 1:
                raise
            last_error = exc
            time.sleep(_RETRY_DELAY_SECONDS)

    raise last_error

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import time


def _to_cents(amount):
    try:
        decimal_amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid order amount: {amount!r}") from exc

    cents = (decimal_amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def charge_customer(order, gateway):
    amount_cents = _to_cents(order["amount"])
    order_id = order["id"]

    max_attempts = 3
    delay_seconds = 0.5

    last_exc = None
    for attempt in range(max_attempts):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            last_exc = exc
            is_last_attempt = attempt == max_attempts - 1
            if is_last_attempt:
                raise
            time.sleep(delay_seconds)

    raise last_exc

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import time


def _to_cents(amount):
    try:
        cents = (Decimal(str(amount)) * Decimal("100")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid order amount: {amount!r}") from exc
    return int(cents)


def charge_customer(order, gateway):
    order_id = order["id"]
    amount_cents = _to_cents(order["amount"])

    delays = (0.1, 0.2, 0.4)
    attempts = len(delays) + 1

    for attempt in range(attempts):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            transient = getattr(exc, "transient", False)
            if not transient or attempt == attempts - 1:
                raise
            time.sleep(delays[attempt])

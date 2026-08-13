from decimal import Decimal, ROUND_HALF_UP
import time


def _to_cents(amount):
    cents = (Decimal(str(amount)) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def charge_customer(order, gateway):
    order_id = order["id"]
    amount_cents = _to_cents(order["amount"])

    max_attempts = 3
    delay_seconds = 0.5

    for attempt in range(1, max_attempts + 1):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            transient = getattr(exc, "transient", False)
            if not transient or attempt == max_attempts:
                raise
            time.sleep(delay_seconds)

from decimal import Decimal, ROUND_HALF_UP


def _to_cents(amount):
    cents = (Decimal(str(amount)) * Decimal("100")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(cents)


def charge_customer(order, gateway):
    order_id = order["id"]
    amount_cents = _to_cents(order["amount"])

    last_error = None
    for _ in range(3):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            transient = getattr(exc, "transient", False)
            if not transient:
                raise
            last_error = exc

    if last_error is not None:
        raise last_error

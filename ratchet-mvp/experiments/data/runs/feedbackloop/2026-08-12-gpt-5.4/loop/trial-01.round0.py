from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


_MAX_RETRIES = 3


def _to_cents(amount):
    try:
        cents = (Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 100)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid order amount") from exc
    return int(cents)


def _is_transient_failure(exc):
    if getattr(exc, "transient", False):
        return True
    name = exc.__class__.__name__.lower()
    return "transient" in name or "timeout" in name or "temporary" in name


def charge_customer(order, gateway):
    amount_cents = _to_cents(order["amount"])
    order_id = order["id"]

    last_exc = None
    for _ in range(_MAX_RETRIES):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            if not _is_transient_failure(exc):
                raise
            last_exc = exc

    raise last_exc

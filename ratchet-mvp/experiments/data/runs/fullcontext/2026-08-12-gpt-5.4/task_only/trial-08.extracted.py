from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


_MAX_RETRIES = 3


def _to_cents(amount):
    try:
        cents = (Decimal(str(amount)) * Decimal("100")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Invalid order amount") from exc
    return int(cents)


def _is_transient_error(exc):
    return getattr(exc, "transient", False) or isinstance(exc, (TimeoutError, ConnectionError))


def charge_customer(order, gateway):
    order_id = order["id"]
    amount_cents = _to_cents(order["amount"])

    last_exc = None
    for attempt in range(_MAX_RETRIES):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            if not _is_transient_error(exc) or attempt == _MAX_RETRIES - 1:
                raise
            last_exc = exc

    raise last_exc

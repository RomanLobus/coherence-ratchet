from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import time


class TransientChargeError(Exception):
    """Raised when a charge cannot be completed after transient failures."""


def _to_cents(amount):
    try:
        cents = (Decimal(str(amount)) * Decimal("100")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"Invalid order amount: {amount!r}") from exc
    return int(cents)


def _is_transient_error(exc):
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True

    transient = getattr(exc, "transient", None)
    if transient is True:
        return True

    code = getattr(exc, "code", None)
    if code in {"timeout", "temporarily_unavailable", "rate_limited"}:
        return True

    return False


def charge_customer(order, gateway):
    order_id = order["id"]
    amount_cents = _to_cents(order["amount"])

    max_attempts = 3
    delays = (0.1, 0.2)

    last_exc = None
    for attempt in range(max_attempts):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            if not _is_transient_error(exc) or attempt == max_attempts - 1:
                if _is_transient_error(exc):
                    raise TransientChargeError(
                        f"Failed to charge order {order_id!r} after {max_attempts} attempts"
                    ) from exc
                raise
            last_exc = exc
            time.sleep(delays[attempt])

    raise TransientChargeError(
        f"Failed to charge order {order_id!r} after {max_attempts} attempts"
    ) from last_exc

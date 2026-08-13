from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import time


class ChargeError(Exception):
    """Raised when a customer charge cannot be completed."""


def _to_cents(amount):
    """
    Convert a monetary amount to integer cents using standard half-up rounding.
    Accepts Decimal-compatible inputs such as str, int, float, or Decimal.
    """
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ChargeError(f"Invalid order amount: {amount!r}") from exc

    cents = (value * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def charge_customer(order, gateway):
    """
    Charge a customer for the given order using the provided gateway.

    The order must contain:
      - order['id']: unique order identifier
      - order['amount']: monetary amount to charge

    The amount is converted to integer cents and submitted via:
      gateway.submit(order['id'], amount_cents)

    Retries on transient failures up to 3 attempts total.
    """
    if not isinstance(order, dict):
        raise ChargeError("Order must be a dictionary.")

    try:
        order_id = order["id"]
        amount = order["amount"]
    except KeyError as exc:
        raise ChargeError(f"Missing required order field: {exc.args[0]}") from exc

    amount_cents = _to_cents(amount)

    max_attempts = 3
    delay_seconds = 0.5

    for attempt in range(1, max_attempts + 1):
        try:
            return gateway.submit(order_id, amount_cents)
        except Exception as exc:
            is_last_attempt = attempt == max_attempts
            is_transient = getattr(exc, "transient", False)

            if not is_transient or is_last_attempt:
                raise

            time.sleep(delay_seconds)

from billing.money import to_cents
from billing.retry import retry


_MAX_RETRIES = 3


def _is_transient_failure(exc):
    if getattr(exc, "transient", False):
        return True
    name = exc.__class__.__name__.lower()
    return "transient" in name or "timeout" in name or "temporary" in name


def charge_customer(order, gateway):
    amount_cents = to_cents(order["amount"])
    order_id = order["id"]

    def submit():
        return gateway.submit(order_id, amount_cents)

    return retry(submit, retries=_MAX_RETRIES, should_retry=_is_transient_failure)

from billing.money import to_minor_units
from billing.resilience import with_backoff


def charge_customer(order, gateway):
    amount_cents = to_minor_units(order["amount"])

    def operation():
        return gateway.submit(order["id"], amount_cents)

    return with_backoff(operation, attempts=3, delay=1)

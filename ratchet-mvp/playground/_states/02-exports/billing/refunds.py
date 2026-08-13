from billing.retry import retry
from billing.money import to_cents


def issue_refund(gateway, order):
    return retry(lambda: gateway.refund(to_cents(order.amount)))

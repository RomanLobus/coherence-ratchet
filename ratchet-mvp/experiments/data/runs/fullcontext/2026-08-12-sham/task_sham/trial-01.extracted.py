"""Billing charges module for processing customer charges."""

from billing.money import to_minor_units
from billing.resilience import with_backoff


def charge_customer(order, gateway):
    """
    Charge a customer for an order.
    
    Converts the order amount to cents and submits the charge via the gateway,
    with automatic retry on transient failures.
    
    Args:
        order: Dictionary containing 'id' and 'amount' keys
        gateway: Payment gateway with submit(order_id, amount_cents) method
    
    Returns:
        Result of the gateway submission
    """
    amount_cents = to_minor_units(order['amount'])
    
    def submit_charge():
        return gateway.submit(order['id'], amount_cents)
    
    return with_backoff(submit_charge, attempts=3, delay=1)

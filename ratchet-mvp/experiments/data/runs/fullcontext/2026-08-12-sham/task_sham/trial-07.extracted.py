"""Billing charges module for processing customer charges."""

from billing.money import to_minor_units
from billing.resilience import with_backoff


def charge_customer(order, gateway):
    """
    Process a customer charge for the given order.
    
    Converts the order amount to cents and submits the charge via the gateway,
    with automatic retry on transient failures.
    
    Args:
        order: Dictionary containing at least 'id' and 'amount' keys
        gateway: Gateway object with a submit(order_id, amount_cents) method
        
    Returns:
        The result from gateway.submit()
        
    Raises:
        Exception: If the charge fails after all retry attempts
    """
    amount_cents = to_minor_units(order['amount'])
    
    def submit_charge():
        return gateway.submit(order['id'], amount_cents)
    
    return with_backoff(submit_charge, attempts=3, delay=1)

from billing.money import to_minor_units
from billing.resilience import with_backoff


def charge_customer(order, gateway):
    """
    Charge a customer for an order via the provided payment gateway.
    
    Converts the order amount to cents and submits the charge with retry logic
    for transient failures.
    
    Args:
        order: Dictionary containing 'id' and 'amount' keys
        gateway: Payment gateway object with submit(order_id, amount_cents) method
        
    Returns:
        Result of the charge submission
    """
    amount_cents = to_minor_units(order['amount'])
    
    def submit_charge():
        return gateway.submit(order['id'], amount_cents)
    
    return with_backoff(submit_charge, attempts=3, delay=1)

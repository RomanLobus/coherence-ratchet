from billing.money import to_minor_units
from billing.resilience import with_backoff


def charge_customer(order, gateway):
    """
    Charge a customer for an order, converting amount to cents and retrying on failure.
    
    Args:
        order: Dictionary containing 'amount' and 'id' keys
        gateway: Payment gateway with submit(order_id, amount_cents) method
        
    Returns:
        Result of the gateway submission
    """
    amount_cents = to_minor_units(order['amount'])
    
    def submit_charge():
        return gateway.submit(order['id'], amount_cents)
    
    return with_backoff(submit_charge, attempts=3, delay=1)

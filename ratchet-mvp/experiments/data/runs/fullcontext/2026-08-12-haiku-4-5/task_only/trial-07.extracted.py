import time
from typing import Any, Dict


def charge_customer(order: Dict[str, Any], gateway: Any) -> Dict[str, Any]:
    """
    Charge a customer for an order using the provided gateway.
    
    Converts the order amount to integer cents and submits the charge via the gateway,
    with retry logic for transient failures.
    
    Args:
        order: Dictionary containing 'id' and 'amount' keys
        gateway: Payment gateway object with a submit method
        
    Returns:
        Dictionary containing the charge result
        
    Raises:
        Exception: If charge fails after all retries
    """
    amount_cents = int(order['amount'] * 100)
    order_id = order['id']
    
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            result = gateway.submit(order_id, amount_cents)
            return result
        except Exception as e:
            # Check if error is transient
            if attempt < max_retries - 1 and _is_transient_error(e):
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise
    
    return {}


def _is_transient_error(error: Exception) -> bool:
    """
    Determine if an error is transient and should be retried.
    
    Args:
        error: The exception that occurred
        
    Returns:
        True if the error is transient, False otherwise
    """
    transient_error_types = (
        ConnectionError,
        TimeoutError,
        IOError,
    )
    
    transient_messages = ['timeout', 'connection', 'temporarily', 'unavailable', 'try again']
    
    if isinstance(error, transient_error_types):
        return True
    
    error_message = str(error).lower()
    return any(msg in error_message for msg in transient_messages)

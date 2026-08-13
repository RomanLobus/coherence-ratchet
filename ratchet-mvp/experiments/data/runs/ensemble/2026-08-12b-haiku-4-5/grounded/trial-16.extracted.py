import uuid
from datetime import datetime, timezone


def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        Dictionary with canonical order structure
    """
    order_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    
    lines = []
    total_cents = 0
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price_cents = item['unit_price_cents']
        
        line = {
            'product_id': product_id,
            'quantity': quantity,
            'unit_price_cents': unit_price_cents
        }
        lines.append(line)
        
        total_cents += quantity * unit_price_cents
    
    return {
        'order_id': order_id,
        'customer_id': customer_id,
        'lines': lines,
        'total_cents': total_cents,
        'currency': 'USD',
        'created_at': created_at
    }

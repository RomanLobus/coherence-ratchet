import uuid
from datetime import datetime


def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', 'unit_price_cents'
    
    Returns:
        Order dictionary with canonical field set
    """
    # Generate order ID
    order_id = str(uuid.uuid4())
    
    # Build lines
    lines = []
    total_cents = 0
    
    for item in items:
        line_total = item['quantity'] * item['unit_price_cents']
        total_cents += line_total
        
        lines.append({
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'unit_price_cents': item['unit_price_cents']
        })
    
    # Create order
    order = {
        'order_id': order_id,
        'customer_id': customer_id,
        'lines': lines,
        'total_cents': total_cents,
        'currency': 'USD',
        'created_at': datetime.utcnow().isoformat()
    }
    
    return order

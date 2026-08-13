import uuid
from datetime import datetime


def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer identifier
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        Dictionary representing the order with canonical field set
    """
    # Calculate total and build lines
    total_cents = 0
    lines = []
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price_cents = item['unit_price_cents']
        
        # Calculate line total
        line_total = quantity * unit_price_cents
        total_cents += line_total
        
        # Add to lines with canonical structure
        lines.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price_cents': unit_price_cents
        })
    
    # Build order with canonical field set
    order = {
        'order_id': str(uuid.uuid4()),
        'customer_id': customer_id,
        'lines': lines,
        'total_cents': total_cents,
        'currency': 'USD',
        'created_at': datetime.utcnow().isoformat()
    }
    
    return order

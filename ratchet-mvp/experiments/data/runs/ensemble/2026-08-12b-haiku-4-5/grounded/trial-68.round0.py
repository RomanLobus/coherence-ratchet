import uuid
from datetime import datetime

def build_order(customer_id, items):
    """
    Build an order dictionary with canonical Order contract fields.
    
    Args:
        customer_id: The customer ID for this order
        items: List of dicts with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        Dictionary with order_id, customer_id, lines, total_cents, currency, created_at
    """
    # Calculate total and build lines
    total_cents = 0
    lines = []
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price_cents = item['unit_price_cents']
        
        line_total = quantity * unit_price_cents
        total_cents += line_total
        
        lines.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price_cents': unit_price_cents
        })
    
    # Build the order with canonical fields
    order = {
        'order_id': str(uuid.uuid4()),
        'customer_id': customer_id,
        'lines': lines,
        'total_cents': total_cents,
        'currency': 'USD',
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    return order

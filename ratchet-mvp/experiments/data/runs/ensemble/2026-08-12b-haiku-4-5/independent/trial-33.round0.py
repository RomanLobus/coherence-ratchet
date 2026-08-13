def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with keys 'product_id', 'quantity', 'unit_price' (in cents)
    
    Returns:
        Dictionary with keys 'customer_id', 'line_items', 'total' (in cents)
    """
    line_items = []
    total = 0
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']
        
        line_total = quantity * unit_price
        total += line_total
        
        line_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'line_total': line_total
        })
    
    return {
        'customer_id': customer_id,
        'line_items': line_items,
        'total': total
    }

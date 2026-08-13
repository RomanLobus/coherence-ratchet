def build_order(customer_id, items):
    """Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer identifier
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    total = 0
    processed_items = []
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']
        
        line_total = quantity * unit_price
        total += line_total
        
        processed_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'line_total': line_total
        })
    
    return {
        'customer_id': customer_id,
        'items': processed_items,
        'total': total
    }

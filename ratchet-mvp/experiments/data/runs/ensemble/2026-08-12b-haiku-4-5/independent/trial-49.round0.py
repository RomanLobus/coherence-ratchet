def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The ID of the customer
        items: List of dictionaries with keys 'product_id', 'quantity', 'unit_price'
               where unit_price is in cents
    
    Returns:
        Dictionary with keys 'customer_id', 'line_items', 'total_cents'
    """
    total_cents = 0
    line_items = []
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']
        
        item_total = quantity * unit_price
        total_cents += item_total
        
        line_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'total_cents': item_total
        })
    
    return {
        'customer_id': customer_id,
        'line_items': line_items,
        'total_cents': total_cents
    }

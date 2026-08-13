def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer's ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with customer, line_items, and order_total (in cents)
    """
    line_items = []
    total_cents = 0
    
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        unit_price = item.get('unit_price')
        
        item_total = quantity * unit_price
        total_cents += item_total
        
        line_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': item_total
        })
    
    return {
        'customer': customer_id,
        'line_items': line_items,
        'order_total': total_cents
    }

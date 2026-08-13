def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: A list of dictionaries, each with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary representing the order with customer, line items, and total
    """
    line_items = []
    total_cents = 0
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']  # in cents
        
        item_total = quantity * unit_price
        total_cents += item_total
        
        line_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': item_total
        })
    
    order = {
        'customer_id': customer_id,
        'line_items': line_items,
        'total': total_cents
    }
    
    return order

def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: A list of dictionaries, each containing:
            - product_id: The product identifier
            - quantity: The quantity ordered
            - unit_price: The price per unit in cents
    
    Returns:
        A dictionary representing the order with:
        - customer_id: The customer ID
        - items: The line items
        - total: The order total in cents
    """
    total_cents = 0
    line_items = []
    
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 0)
        unit_price = item.get('unit_price', 0)
        
        item_total = quantity * unit_price
        total_cents += item_total
        
        line_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': item_total
        })
    
    return {
        'customer_id': customer_id,
        'items': line_items,
        'total': total_cents
    }

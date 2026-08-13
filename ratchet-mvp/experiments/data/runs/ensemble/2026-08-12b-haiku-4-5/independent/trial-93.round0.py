def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: A list of dictionaries, each containing:
            - product_id: The ID of the product
            - quantity: The quantity ordered
            - unit_price: The price in cents
    
    Returns:
        A dictionary containing:
            - customer_id: The customer ID
            - items: The line items with extended prices
            - total: The order total in cents
    """
    line_items = []
    total_cents = 0
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']
        
        extended_price = quantity * unit_price
        total_cents += extended_price
        
        line_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'extended_price': extended_price
        })
    
    return {
        'customer_id': customer_id,
        'items': line_items,
        'total': total_cents
    }

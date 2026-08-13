def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer identifier
        items: A list of dictionaries, each containing:
            - product_id: The product identifier
            - quantity: The quantity ordered
            - unit_price: The price per unit in cents
    
    Returns:
        A dictionary representing the order with:
        - customer_id: The customer identifier
        - line_items: List of items in the order
        - order_total: Total price in cents
    """
    order_total = 0
    line_items = []
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']
        
        line_total = quantity * unit_price
        order_total += line_total
        
        line_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'line_total': line_total
        })
    
    return {
        'customer_id': customer_id,
        'line_items': line_items,
        'order_total': order_total
    }

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
        A dictionary representing the order with:
        - customer_id: The customer ID
        - line_items: The list of items
        - order_total: The total order amount in cents
    """
    order_total = 0
    
    for item in items:
        line_total = item['quantity'] * item['unit_price']
        order_total += line_total
    
    return {
        'customer_id': customer_id,
        'line_items': items,
        'order_total': order_total
    }

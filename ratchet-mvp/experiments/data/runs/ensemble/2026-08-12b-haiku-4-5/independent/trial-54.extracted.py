def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The ID of the customer
        items: A list of dictionaries, each containing:
            - product_id: The product ID
            - quantity: The quantity ordered
            - unit_price: The unit price in cents
    
    Returns:
        A dictionary representing the order with:
        - customer_id: The customer ID
        - items: The line items with extended prices
        - total: The order total in cents
    """
    line_items = []
    order_total = 0
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']
        
        extended_price = quantity * unit_price
        order_total += extended_price
        
        line_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'extended_price': extended_price
        })
    
    return {
        'customer_id': customer_id,
        'items': line_items,
        'total': order_total
    }

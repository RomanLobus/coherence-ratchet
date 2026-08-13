def build_order(customer_id, items):
    """Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer ID
        items: A list of dictionaries, each containing:
               - product_id: The product identifier
               - quantity: The quantity ordered
               - unit_price: The price in cents
    
    Returns:
        A dictionary containing:
        - customer_id: The customer ID
        - line_items: The list of items
        - order_total: The total order amount in cents
    """
    order_total = 0
    line_items = []
    
    for item in items:
        line_total = item['quantity'] * item['unit_price']
        order_total += line_total
        
        line_item = {
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'unit_price': item['unit_price'],
            'line_total': line_total
        }
        line_items.append(line_item)
    
    return {
        'customer_id': customer_id,
        'line_items': line_items,
        'order_total': order_total
    }

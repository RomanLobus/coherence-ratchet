def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items list.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: List of dictionaries, each containing:
            - product_id: The product identifier
            - quantity: The quantity ordered
            - unit_price: The price per unit in cents
    
    Returns:
        A dictionary representing the order with:
            - customer_id: The customer placing the order
            - line_items: The list of items with calculated totals
            - order_total: The total order amount in cents
    """
    line_items = []
    order_total_cents = 0
    
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 0)
        unit_price = item.get('unit_price', 0)
        
        item_total = quantity * unit_price
        
        line_item = {
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': item_total
        }
        line_items.append(line_item)
        order_total_cents += item_total
    
    order = {
        'customer_id': customer_id,
        'line_items': line_items,
        'order_total': order_total_cents
    }
    
    return order

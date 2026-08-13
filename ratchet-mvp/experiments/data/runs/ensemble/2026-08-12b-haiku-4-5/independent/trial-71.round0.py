def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: List of dictionaries, each containing:
               - product_id: The product identifier
               - quantity: The quantity ordered
               - unit_price: The unit price in cents
    
    Returns:
        A dictionary containing:
        - customer_id: The customer ID
        - items: List of line items with product_id, quantity, unit_price, and total
        - order_total: The total order amount in cents
    """
    line_items = []
    order_total = 0
    
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        unit_price = item.get('unit_price')
        
        item_total = quantity * unit_price
        order_total += item_total
        
        line_item = {
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': item_total
        }
        line_items.append(line_item)
    
    return {
        'customer_id': customer_id,
        'items': line_items,
        'order_total': order_total
    }

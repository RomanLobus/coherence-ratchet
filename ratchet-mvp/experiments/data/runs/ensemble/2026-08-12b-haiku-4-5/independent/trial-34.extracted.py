def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items list.
    
    Args:
        customer_id: The ID of the customer
        items: List of dictionaries with keys:
            - product_id: The product identifier
            - quantity: The quantity ordered
            - unit_price: The unit price in cents
    
    Returns:
        Dictionary with keys:
            - customer_id: The customer ID
            - items: The line items with extended prices
            - total: The order total in cents
    """
    line_items = []
    total_cents = 0
    
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 0)
        unit_price = item.get('unit_price', 0)
        
        extended_price = quantity * unit_price
        total_cents += extended_price
        
        line_item = {
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'extended_price': extended_price
        }
        line_items.append(line_item)
    
    order = {
        'customer_id': customer_id,
        'items': line_items,
        'total': total_cents
    }
    
    return order

def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items list.
    
    Args:
        customer_id: The customer ID for this order
        items: List of dictionaries with keys:
            - product_id: The product identifier
            - quantity: Number of units ordered
            - unit_price: Price per unit in cents
    
    Returns:
        Dictionary with keys:
            - customer_id: The customer ID
            - line_items: The list of items (with calculated totals)
            - order_total: Total order amount in cents
    """
    line_items = []
    total_cents = 0
    
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 0)
        unit_price = item.get('unit_price', 0)
        
        item_total = quantity * unit_price
        total_cents += item_total
        
        line_item = {
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': item_total
        }
        line_items.append(line_item)
    
    return {
        'customer_id': customer_id,
        'line_items': line_items,
        'order_total': total_cents
    }

def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items list.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: List of dictionaries with keys:
            - product_id: ID of the product
            - quantity: Number of units ordered
            - unit_price: Price per unit in cents
    
    Returns:
        Dictionary with keys:
            - customer_id: The customer ID
            - line_items: List of line items with subtotal calculated
            - order_total: Total order amount in cents
    """
    line_items = []
    total_cents = 0
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']
        
        subtotal = quantity * unit_price
        total_cents += subtotal
        
        line_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'subtotal': subtotal
        })
    
    return {
        'customer_id': customer_id,
        'line_items': line_items,
        'order_total': total_cents
    }

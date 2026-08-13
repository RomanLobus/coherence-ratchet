def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items list.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer', 'line_items', and 'order_total' (in cents)
    """
    line_items = []
    total_cents = 0
    
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 0)
        unit_price = item.get('unit_price', 0)
        
        # Calculate line item total in cents
        line_total = quantity * unit_price
        total_cents += line_total
        
        # Create line item dictionary
        line_item = {
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'line_total': line_total
        }
        line_items.append(line_item)
    
    # Build and return the order
    order = {
        'customer': customer_id,
        'line_items': line_items,
        'order_total': total_cents
    }
    
    return order

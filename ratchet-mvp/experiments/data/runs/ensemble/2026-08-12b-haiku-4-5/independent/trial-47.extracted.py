def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The ID of the customer
        items: List of dictionaries with keys 'product_id', 'quantity', 'unit_price'
               (unit_price is in cents)
    
    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    total = 0
    line_items = []
    
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 0)
        unit_price = item.get('unit_price', 0)
        
        # Calculate line item total
        line_total = quantity * unit_price
        total += line_total
        
        # Build line item
        line_item = {
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': line_total
        }
        line_items.append(line_item)
    
    # Build and return order
    order = {
        'customer_id': customer_id,
        'items': line_items,
        'total': total
    }
    
    return order

def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: A list of dictionaries, each with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary containing the customer ID, line items, and order total (in cents)
    """
    line_items = []
    total_cents = 0
    
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 0)
        unit_price = item.get('unit_price', 0)
        
        # Calculate line total in cents
        line_total = quantity * unit_price
        total_cents += line_total
        
        # Create line item entry
        line_item = {
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'line_total': line_total
        }
        line_items.append(line_item)
    
    # Build the order dictionary
    order = {
        'customer_id': customer_id,
        'line_items': line_items,
        'order_total': total_cents
    }
    
    return order

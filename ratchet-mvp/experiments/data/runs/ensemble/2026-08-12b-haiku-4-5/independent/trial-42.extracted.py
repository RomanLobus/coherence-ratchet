def build_order(customer_id, items):
    """
    Build an order dictionary from customer_id and items.
    
    Args:
        customer_id: The ID of the customer
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary with 'customer_id', 'line_items', and 'total' (in cents)
    """
    if not isinstance(items, list):
        raise ValueError("items must be a list")
    
    line_items = []
    total_cents = 0
    
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Each item must be a dictionary")
        
        required_keys = {'product_id', 'quantity', 'unit_price'}
        if not required_keys.issubset(item.keys()):
            raise ValueError(f"Each item must contain {required_keys}")
        
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']
        
        if not isinstance(quantity, (int, float)) or quantity < 0:
            raise ValueError(f"quantity must be a non-negative number")
        if not isinstance(unit_price, (int, float)) or unit_price < 0:
            raise ValueError(f"unit_price must be a non-negative number")
        
        line_total = int(quantity * unit_price)
        total_cents += line_total
        
        line_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'line_total': line_total
        })
    
    return {
        'customer_id': customer_id,
        'line_items': line_items,
        'total': total_cents
    }

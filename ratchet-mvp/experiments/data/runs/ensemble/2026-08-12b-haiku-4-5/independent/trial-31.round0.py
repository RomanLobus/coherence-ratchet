"""Module for building customer orders."""


def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer identifier
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
        
    Returns:
        Dictionary with 'customer_id', 'items', and 'order_total' (in cents)
    """
    line_items = []
    total_cents = 0
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']
        
        # Calculate line item total
        line_total = quantity * unit_price
        total_cents += line_total
        
        line_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'line_total': line_total
        })
    
    return {
        'customer_id': customer_id,
        'items': line_items,
        'order_total': total_cents
    }

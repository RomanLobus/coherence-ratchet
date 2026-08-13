"""Module for building customer orders."""


def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items list.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary containing 'customer_id', 'items', and 'total' (in cents)
    """
    total = 0
    line_items = []
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']
        
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

"""Module for building customer orders."""


def build_order(customer_id: str, items: list[dict]) -> dict:
    """Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The ID of the customer
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
        
    Returns:
        A dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    line_items = []
    total = 0
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']
        
        item_total = quantity * unit_price
        total += item_total
        
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
        'total': total
    }

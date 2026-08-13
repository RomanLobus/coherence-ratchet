"""Module for building orders from customer and item data."""


def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: A list of dictionaries, each containing:
               - product_id: The ID of the product
               - quantity: The quantity ordered
               - unit_price: The price in cents
    
    Returns:
        A dictionary containing:
        - customer_id: The customer ID
        - line_items: The list of items with calculated totals
        - total: The total order amount in cents
    """
    line_items = []
    order_total = 0
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']
        
        # Calculate line item total
        line_total = quantity * unit_price
        order_total += line_total
        
        # Create line item with total
        line_item = {
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': line_total
        }
        line_items.append(line_item)
    
    # Build and return the order
    return {
        'customer_id': customer_id,
        'line_items': line_items,
        'total': order_total
    }

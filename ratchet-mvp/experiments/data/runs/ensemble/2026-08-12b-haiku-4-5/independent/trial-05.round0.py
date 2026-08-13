"""Module for building customer orders."""


def build_order(customer_id, items):
    """Build an order dictionary from customer ID and line items.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: List of dictionaries, each containing:
            - 'product_id': The ID of the product
            - 'quantity': The quantity ordered
            - 'unit_price': The price in cents
    
    Returns:
        A dictionary representing the order with:
            - 'customer_id': The customer ID
            - 'line_items': List of line item dictionaries with product_id, quantity, unit_price, and total
            - 'order_total': The total order amount in cents
    """
    line_items = []
    order_total = 0
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']
        
        item_total = quantity * unit_price
        order_total += item_total
        
        line_item = {
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': item_total
        }
        line_items.append(line_item)
    
    order = {
        'customer_id': customer_id,
        'line_items': line_items,
        'order_total': order_total
    }
    
    return order

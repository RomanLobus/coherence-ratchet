"""Module for building orders from customer and item information."""


def build_order(customer_id, items):
    """Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The ID of the customer placing the order.
        items: A list of dictionaries, each containing:
            - product_id: The ID of the product
            - quantity: The quantity ordered
            - unit_price: The price per unit in cents
    
    Returns:
        A dictionary with keys:
            - customer_id: The customer ID
            - items: The list of items with line totals
            - total: The total order amount in cents
    """
    line_items = []
    total = 0
    
    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price = item["unit_price"]
        line_total = quantity * unit_price
        total += line_total
        
        line_items.append({
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "line_total": line_total,
        })
    
    return {
        "customer_id": customer_id,
        "items": line_items,
        "total": total,
    }

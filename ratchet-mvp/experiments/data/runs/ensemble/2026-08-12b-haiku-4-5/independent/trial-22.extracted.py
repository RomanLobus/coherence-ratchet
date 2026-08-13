def build_order(customer_id, items):
    """
    Build a dictionary representing a customer order.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: A list of dictionaries, each containing:
               - product_id: The product identifier
               - quantity: The quantity ordered
               - unit_price: The unit price in cents
    
    Returns:
        A dictionary with keys:
        - customer: The customer ID
        - items: The line items from the input
        - total: The order total in cents
    """
    total = 0
    
    for item in items:
        line_total = item["quantity"] * item["unit_price"]
        total += line_total
    
    return {
        "customer": customer_id,
        "items": items,
        "total": total
    }

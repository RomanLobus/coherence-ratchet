def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items list.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: List of dictionaries, each containing:
            - product_id: The ID of the product
            - quantity: The quantity ordered
            - unit_price: The price per unit in cents
    
    Returns:
        A dictionary representing the order with:
        - customer_id: The customer ID
        - items: The line items
        - total: The order total in cents
    """
    total_cents = 0
    
    # Calculate the total from all items
    for item in items:
        line_total = item["quantity"] * item["unit_price"]
        total_cents += line_total
    
    # Build and return the order dictionary
    return {
        "customer_id": customer_id,
        "items": items,
        "total": total_cents
    }

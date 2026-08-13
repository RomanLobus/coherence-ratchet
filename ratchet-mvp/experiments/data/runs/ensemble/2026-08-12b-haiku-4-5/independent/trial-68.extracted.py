def build_order(customer_id, items):
    """
    Build an order dictionary for a customer.
    
    Args:
        customer_id: The ID of the customer
        items: A list of dictionaries, each containing:
            - product_id: The ID of the product
            - quantity: The quantity ordered
            - unit_price: The price in cents
    
    Returns:
        A dictionary with the following structure:
        {
            "customer_id": <customer_id>,
            "items": [list of items],
            "total": <total in cents>
        }
    """
    order_total = 0
    line_items = []
    
    for item in items:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 0)
        unit_price = item.get("unit_price", 0)
        
        line_total = quantity * unit_price
        order_total += line_total
        
        line_items.append({
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "total": line_total
        })
    
    return {
        "customer_id": customer_id,
        "items": line_items,
        "total": order_total
    }

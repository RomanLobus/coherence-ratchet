import uuid
from datetime import datetime


def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items list.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        A dictionary representing the order with canonical fields
    """
    # Generate a unique order ID
    order_id = str(uuid.uuid4())
    
    # Build the lines array with exactly the required fields
    lines = []
    total_cents = 0
    
    for item in items:
        line_item = {
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price_cents": item["unit_price_cents"]
        }
        lines.append(line_item)
        
        # Calculate total
        total_cents += item["quantity"] * item["unit_price_cents"]
    
    # Create the order with exactly the required top-level fields
    order = {
        "order_id": order_id,
        "customer_id": customer_id,
        "lines": lines,
        "total_cents": total_cents,
        "currency": "USD",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return order

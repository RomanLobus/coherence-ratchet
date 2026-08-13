import uuid
from datetime import datetime


def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items list.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with keys: product_id, quantity, unit_price_cents
    
    Returns:
        Dictionary with keys: order_id, customer_id, lines, total_cents, currency, created_at
    """
    # Generate a unique order ID
    order_id = str(uuid.uuid4())
    
    # Build lines from items and calculate total
    lines = []
    total_cents = 0
    
    for item in items:
        line = {
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price_cents": item["unit_price_cents"]
        }
        lines.append(line)
        total_cents += item["quantity"] * item["unit_price_cents"]
    
    # Create the order dictionary with required fields
    order = {
        "order_id": order_id,
        "customer_id": customer_id,
        "lines": lines,
        "total_cents": total_cents,
        "currency": "USD",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return order

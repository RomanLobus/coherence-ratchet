import uuid
from datetime import datetime


def build_order(customer_id, items):
    """Build a canonical order dictionary from customer_id and items.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        A dictionary representing the order with canonical field names
    """
    # Generate a unique order ID
    order_id = str(uuid.uuid4())
    
    # Process line items and calculate total
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
    
    # Create the order with canonical field set
    order = {
        "order_id": order_id,
        "customer_id": customer_id,
        "lines": lines,
        "total_cents": total_cents,
        "currency": "USD",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return order

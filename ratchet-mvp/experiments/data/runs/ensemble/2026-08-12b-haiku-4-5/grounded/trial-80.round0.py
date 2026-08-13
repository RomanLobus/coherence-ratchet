import uuid
from datetime import datetime


def build_order(customer_id, items):
    """
    Build an order dictionary from customer_id and items list.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', and 'unit_price_cents' keys
    
    Returns:
        Dictionary representing a complete order with the canonical field set
    """
    order_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat() + "Z"
    
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
    
    order = {
        "order_id": order_id,
        "customer_id": customer_id,
        "lines": lines,
        "total_cents": total_cents,
        "currency": "USD",
        "created_at": created_at
    }
    
    return order

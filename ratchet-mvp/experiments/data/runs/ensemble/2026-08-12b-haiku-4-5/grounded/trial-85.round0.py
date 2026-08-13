import uuid
from datetime import datetime


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with keys: product_id, quantity, unit_price_cents
    
    Returns:
        Dictionary representing the order with canonical field set
    """
    lines = []
    total_cents = 0
    
    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]
        
        line_total = quantity * unit_price_cents
        total_cents += line_total
        
        lines.append({
            "product_id": product_id,
            "quantity": quantity,
            "unit_price_cents": unit_price_cents
        })
    
    order = {
        "order_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "lines": lines,
        "total_cents": total_cents,
        "currency": "USD",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return order

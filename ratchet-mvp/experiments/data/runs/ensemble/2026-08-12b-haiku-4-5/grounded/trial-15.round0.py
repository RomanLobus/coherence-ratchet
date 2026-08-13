import uuid
from datetime import datetime, timezone


def build_order(customer_id, items):
    """
    Build an order dictionary from customer_id and items list.
    
    Args:
        customer_id: The customer ID for this order
        items: List of dictionaries with keys: product_id, quantity, unit_price_cents
        
    Returns:
        Dictionary with canonical Order contract fields:
        order_id, customer_id, lines, total_cents, currency, created_at
    """
    # Generate a unique order ID
    order_id = str(uuid.uuid4())
    
    # Build the lines array with canonical field set
    lines = []
    total_cents = 0
    
    for item in items:
        line_total = item["quantity"] * item["unit_price_cents"]
        total_cents += line_total
        
        lines.append({
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price_cents": item["unit_price_cents"]
        })
    
    # Create the order with canonical field set
    order = {
        "order_id": order_id,
        "customer_id": customer_id,
        "lines": lines,
        "total_cents": total_cents,
        "currency": "USD",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    return order

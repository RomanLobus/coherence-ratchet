import uuid
from datetime import datetime


def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: List of dictionaries with keys:
               - product_id: Product identifier
               - quantity: Number of units
               - unit_price_cents: Price per unit in cents
    
    Returns:
        Dictionary representing the order with canonical field set:
        - order_id: Unique order identifier
        - customer_id: Customer identifier
        - lines: List of line items
        - total_cents: Total order amount in cents
        - currency: Currency code
        - created_at: ISO 8601 timestamp
    """
    lines = []
    total_cents = 0
    
    for item in items:
        line_total = item["quantity"] * item["unit_price_cents"]
        lines.append({
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price_cents": item["unit_price_cents"]
        })
        total_cents += line_total
    
    return {
        "order_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "lines": lines,
        "total_cents": total_cents,
        "currency": "USD",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

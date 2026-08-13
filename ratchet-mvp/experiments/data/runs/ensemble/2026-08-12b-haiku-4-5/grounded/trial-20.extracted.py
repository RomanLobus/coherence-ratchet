"""Order building module for constructing canonical order dictionaries."""

import uuid
from datetime import datetime


def build_order(customer_id, items):
    """
    Build a canonical order dictionary from customer and items data.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with keys: product_id, quantity, unit_price_cents
        
    Returns:
        Dictionary with canonical Order contract structure:
        - order_id
        - customer_id
        - lines (list of dicts with product_id, quantity, unit_price_cents)
        - total_cents
        - currency
        - created_at
    """
    total_cents = 0
    lines = []
    
    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]
        
        line_total = quantity * unit_price_cents
        total_cents += line_total
        
        lines.append({
            "product_id": product_id,
            "quantity": quantity,
            "unit_price_cents": unit_price_cents,
        })
    
    return {
        "order_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "lines": lines,
        "total_cents": total_cents,
        "currency": "USD",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

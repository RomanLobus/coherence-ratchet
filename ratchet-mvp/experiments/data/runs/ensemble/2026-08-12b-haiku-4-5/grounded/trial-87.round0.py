"""Order building module for constructing canonical order structures."""

import uuid
from datetime import datetime, timezone


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build a canonical order from customer ID and items.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with keys: product_id, quantity, unit_price_cents
    
    Returns:
        A canonical order dict with keys:
        order_id, customer_id, lines, total_cents, currency, created_at
    """
    lines = []
    total_cents = 0
    
    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]
        
        line = {
            "product_id": product_id,
            "quantity": quantity,
            "unit_price_cents": unit_price_cents,
        }
        lines.append(line)
        total_cents += quantity * unit_price_cents
    
    order = {
        "order_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "lines": lines,
        "total_cents": total_cents,
        "currency": "USD",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    return order

"""
Order builder module that constructs order dictionaries conforming to the canonical schema.
"""

import uuid
from datetime import datetime


def build_order(customer_id, items):
    """
    Build an order dictionary from customer_id and items list.
    
    Args:
        customer_id: The unique identifier for the customer
        items: List of dictionaries, each containing:
            - product_id: The product identifier
            - quantity: Number of units
            - unit_price_cents: Price per unit in cents
    
    Returns:
        A dictionary representing the order with canonical fields:
        - order_id: Unique identifier for the order
        - customer_id: The customer who placed the order
        - lines: List of line items with product_id, quantity, unit_price_cents
        - total_cents: Total order amount in cents
        - currency: Currency code (default USD)
        - created_at: ISO format timestamp
    """
    # Generate unique order ID
    order_id = str(uuid.uuid4())
    
    # Process line items and calculate total
    lines = []
    total_cents = 0
    
    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]
        
        # Add to lines with canonical field names
        lines.append({
            "product_id": product_id,
            "quantity": quantity,
            "unit_price_cents": unit_price_cents
        })
        
        # Accumulate total
        total_cents += quantity * unit_price_cents
    
    # Build the order with canonical fields
    order = {
        "order_id": order_id,
        "customer_id": customer_id,
        "lines": lines,
        "total_cents": total_cents,
        "currency": "USD",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return order

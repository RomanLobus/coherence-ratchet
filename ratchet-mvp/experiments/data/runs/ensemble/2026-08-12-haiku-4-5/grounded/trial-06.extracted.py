import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id: str, items: list) -> dict:
    """
    Build an order using Claude to validate and process the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', 'unit_price_cents'
    
    Returns:
        A dictionary representing the order with canonical fields
    """
    client = anthropic.Anthropic()
    
    order_id = str(uuid4())
    created_at = datetime.utcnow().isoformat() + "Z"
    total_cents = sum(item.get("quantity", 0) * item.get("unit_price_cents", 0) for item in items)
    
    lines = []
    for item in items:
        lines.append({
            "product_id": item.get("product_id"),
            "quantity": item.get("quantity"),
            "unit_price_cents": item.get("unit_price_cents")
        })
    
    order_data = {
        "order_id": order_id,
        "customer_id": customer_id,
        "lines": lines,
        "total_cents": total_cents,
        "currency": "USD",
        "created_at": created_at
    }
    
    prompt = f"""Validate this order structure and confirm it follows the canonical format. 
The order must have exactly these top-level keys: order_id, customer_id, lines, total_cents, currency, created_at
Each line item must have exactly: product_id, quantity, unit_price_cents

Order to validate:
{json.dumps(order_data, indent=2)}

Respond with only 'VALID' if the structure is correct, or describe the issue if not."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    validation_result = message.content[0].text.strip()
    if "VALID" not in validation_result.upper():
        raise ValueError(f"Order validation failed: {validation_result}")
    
    return order_data

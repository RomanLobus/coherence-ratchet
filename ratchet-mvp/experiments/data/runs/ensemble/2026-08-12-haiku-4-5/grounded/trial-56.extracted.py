"""Build order objects according to the canonical Order contract."""

import anthropic
import json
from datetime import datetime
import uuid


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with keys: product_id, quantity, unit_price_cents
        
    Returns:
        Dictionary with keys: order_id, customer_id, lines, total_cents, currency, created_at
    """
    client = anthropic.Anthropic()
    
    prompt = f"""You are an order builder. Given a customer ID and a list of items, construct a valid order object.

Customer ID: {customer_id}

Items:
{json.dumps(items, indent=2)}

Generate a complete order following this structure:
- order_id: a unique UUID string
- customer_id: the provided customer ID
- lines: array where each item has product_id, quantity, unit_price_cents
- total_cents: sum of (quantity * unit_price_cents) for all items
- currency: "USD" 
- created_at: ISO 8601 timestamp

Return ONLY valid JSON matching this exact structure, no additional text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    
    try:
        order = json.loads(response_text)
    except json.JSONDecodeError:
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            order = json.loads(response_text[json_start:json_end])
        else:
            order = {
                "order_id": str(uuid.uuid4()),
                "customer_id": customer_id,
                "lines": items,
                "total_cents": sum(item.get("quantity", 0) * item.get("unit_price_cents", 0) for item in items),
                "currency": "USD",
                "created_at": datetime.utcnow().isoformat() + "Z"
            }
    
    required_keys = {"order_id", "customer_id", "lines", "total_cents", "currency", "created_at"}
    if not all(key in order for key in required_keys):
        order = {
            "order_id": order.get("order_id", str(uuid.uuid4())),
            "customer_id": customer_id,
            "lines": order.get("lines", items),
            "total_cents": order.get("total_cents", sum(item.get("quantity", 0) * item.get("unit_price_cents", 0) for item in items)),
            "currency": order.get("currency", "USD"),
            "created_at": order.get("created_at", datetime.utcnow().isoformat() + "Z")
        }
    
    for line in order.get("lines", []):
        required_line_keys = {"product_id", "quantity", "unit_price_cents"}
        if not all(key in line for key in required_line_keys):
            line.update({
                "product_id": line.get("product_id", "unknown"),
                "quantity": line.get("quantity", 0),
                "unit_price_cents": line.get("unit_price_cents", 0)
            })
    
    return order

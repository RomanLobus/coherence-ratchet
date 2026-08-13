import anthropic
import json
from datetime import datetime
import uuid


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        Order dictionary with canonical fields: order_id, customer_id, lines, 
        total_cents, currency, created_at
    """
    client = anthropic.Anthropic()
    
    prompt = f"""You are a precise order builder. Given the following items for a customer, 
calculate the order total and return a valid JSON order object.

Customer ID: {customer_id}
Items: {json.dumps(items)}

Return ONLY a valid JSON object (no markdown, no extra text) with these exact fields:
- order_id: a UUID string
- customer_id: the customer ID provided
- lines: array of objects with product_id, quantity, unit_price_cents
- total_cents: sum of (quantity * unit_price_cents) for all lines
- currency: "USD"
- created_at: current ISO 8601 timestamp

The order object must have exactly these top-level keys and no others."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    if "order_id" not in order:
        order["order_id"] = str(uuid.uuid4())
    if "customer_id" not in order:
        order["customer_id"] = customer_id
    if "currency" not in order:
        order["currency"] = "USD"
    if "created_at" not in order:
        order["created_at"] = datetime.utcnow().isoformat() + "Z"
    
    if "lines" not in order:
        order["lines"] = items
    
    if "total_cents" not in order:
        total = sum(item["quantity"] * item["unit_price_cents"] for item in order["lines"])
        order["total_cents"] = total
    
    return order

import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with product_id, quantity, and unit_price_cents
    
    Returns:
        A dictionary representing the order with canonical field set
    """
    
    client = anthropic.Anthropic()
    
    items_text = json.dumps(items, indent=2)
    
    prompt = f"""You are an order processing system. Given the following items for a customer order, 
create a valid order object.

Customer ID: {customer_id}
Items:
{items_text}

Return ONLY a valid JSON object with this exact structure:
{{
  "order_id": "<generated UUID>",
  "customer_id": "{customer_id}",
  "lines": [
    {{"product_id": "...", "quantity": <number>, "unit_price_cents": <number>}},
    ...
  ],
  "total_cents": <calculated total>,
  "currency": "USD",
  "created_at": "<ISO 8601 timestamp>"
}}

Calculate total_cents by summing (quantity * unit_price_cents) for each line.
Use current timestamp for created_at in ISO 8601 format."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    
    order = json.loads(response_text)
    
    valid_keys = {"order_id", "customer_id", "lines", "total_cents", "currency", "created_at"}
    if set(order.keys()) != valid_keys:
        raise ValueError(f"Order has invalid top-level keys. Expected {valid_keys}, got {set(order.keys())}")
    
    for line in order["lines"]:
        line_keys = {"product_id", "quantity", "unit_price_cents"}
        if set(line.keys()) != line_keys:
            raise ValueError(f"Line item has invalid keys. Expected {line_keys}, got {set(line.keys())}")
    
    return order


if __name__ == "__main__":
    sample_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price_cents": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price_cents": 4999}
    ]
    
    order = build_order("CUST123", sample_items)
    print(json.dumps(order, indent=2))

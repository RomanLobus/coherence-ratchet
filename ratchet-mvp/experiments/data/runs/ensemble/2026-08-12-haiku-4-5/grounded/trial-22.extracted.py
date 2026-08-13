import anthropic
import json
from datetime import datetime
import uuid


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and structure the data.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', 'unit_price_cents'
    
    Returns:
        A dictionary representing the order with canonical field set
    """
    client = anthropic.Anthropic()
    
    items_json = json.dumps(items, indent=2)
    
    prompt = f"""Given the following customer ID and items, create a valid order object.

Customer ID: {customer_id}

Items (each with product_id, quantity, unit_price_cents):
{items_json}

Return ONLY a valid JSON object with these exact top-level keys:
- order_id (a UUID string)
- customer_id (the provided customer ID)
- lines (array of objects with product_id, quantity, unit_price_cents)
- total_cents (sum of quantity * unit_price_cents for all lines)
- currency (use "USD")
- created_at (ISO 8601 timestamp)

Example format:
{{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": "cust_123",
  "lines": [
    {{"product_id": "prod_1", "quantity": 2, "unit_price_cents": 1000}},
    {{"product_id": "prod_2", "quantity": 1, "unit_price_cents": 2500}}
  ],
  "total_cents": 4500,
  "currency": "USD",
  "created_at": "2025-01-15T10:30:00Z"
}}

Return only the JSON object, no other text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order

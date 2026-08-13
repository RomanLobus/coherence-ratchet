import anthropic
import json
from datetime import datetime
import uuid


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dicts with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        Dictionary representing the order with canonical fields
    """
    client = anthropic.Anthropic()
    
    prompt = f"""Given the following customer order request, validate the data and return a properly formatted JSON order object.

Customer ID: {customer_id}
Items: {json.dumps(items)}

Return ONLY a valid JSON object (no markdown, no explanation) with these exact top-level keys:
- order_id (string, generate a UUID)
- customer_id (string, use the provided value)
- lines (array of objects with product_id, quantity, unit_price_cents)
- total_cents (integer, sum of quantity * unit_price_cents for all lines)
- currency (string, use "USD")
- created_at (string, ISO 8601 timestamp)

Validate that:
1. Each item has product_id, quantity, and unit_price_cents
2. quantity and unit_price_cents are positive integers
3. Calculate the total correctly

Return the JSON object only."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    order_data = json.loads(response_text)
    
    return order_data

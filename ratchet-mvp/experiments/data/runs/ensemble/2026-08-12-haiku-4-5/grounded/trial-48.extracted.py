import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', 'unit_price_cents'
    
    Returns:
        A dictionary representing the order with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Calculate total
    total_cents = sum(item['quantity'] * item['unit_price_cents'] for item in items)
    
    # Prepare the prompt for Claude to validate and structure the order
    prompt = f"""You are an order processing system. Given the following order data, validate it and return a JSON object with the exact structure specified.

Customer ID: {customer_id}
Items: {json.dumps(items)}
Total Cents: {total_cents}

Return ONLY a valid JSON object (no markdown, no explanation) with these exact top-level keys:
- order_id (string, unique identifier)
- customer_id (string)
- lines (array of objects with: product_id, quantity, unit_price_cents)
- total_cents (integer)
- currency (string, default "USD")
- created_at (ISO 8601 timestamp string)

Validate that:
1. All required fields are present
2. Quantities are positive integers
3. Unit prices are positive integers
4. Total equals sum of (quantity * unit_price_cents)
5. Items list is not empty"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    
    # Claude should return valid JSON, but handle potential formatting
    try:
        order = json.loads(response_text)
    except json.JSONDecodeError:
        # If Claude wrapped it in markdown, extract the JSON
        if "
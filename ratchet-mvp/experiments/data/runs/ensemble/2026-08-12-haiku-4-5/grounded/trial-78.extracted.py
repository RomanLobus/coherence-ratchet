import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id, items):
    """
    Build an Order contract using Claude.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', 'unit_price_cents'
    
    Returns:
        Dictionary with canonical Order contract fields
    """
    client = anthropic.Anthropic()
    
    # Create the prompt for Claude to validate and structure the order
    prompt = f"""You are an order builder. Given a customer ID and a list of items, construct a valid Order contract.

Customer ID: {customer_id}
Items: {json.dumps(items)}

Return ONLY a valid JSON object with exactly these top-level keys:
- order_id: A unique identifier (use UUID format)
- customer_id: The provided customer ID
- lines: Array of line items, each with product_id, quantity, unit_price_cents
- total_cents: Sum of (quantity * unit_price_cents) for all lines
- currency: "USD"
- created_at: ISO 8601 timestamp

Respond with ONLY the JSON object, no markdown, no explanation."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order

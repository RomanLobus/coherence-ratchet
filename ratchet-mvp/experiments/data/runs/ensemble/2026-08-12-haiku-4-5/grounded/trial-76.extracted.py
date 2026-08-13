import anthropic
import json
import uuid
from datetime import datetime


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dicts with keys: product_id, quantity, unit_price_cents
    
    Returns:
        A dictionary with canonical order fields: order_id, customer_id, lines, 
        total_cents, currency, created_at
    """
    
    # Create the client
    client = anthropic.Anthropic()
    
    # Prepare the order data for Claude validation
    order_data = {
        "customer_id": customer_id,
        "items": items
    }
    
    # Use Claude to validate and structure the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are an order processing system. Given the following order data, 
return a valid order JSON object with these exact fields:
- order_id (a UUID string)
- customer_id (from input)
- lines (array of objects with: product_id, quantity, unit_price_cents)
- total_cents (sum of quantity * unit_price_cents for all lines)
- currency (always "USD")
- created_at (current ISO 8601 timestamp)

Input order data:
{json.dumps(order_data)}

Return ONLY valid JSON, no other text."""
            }
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order

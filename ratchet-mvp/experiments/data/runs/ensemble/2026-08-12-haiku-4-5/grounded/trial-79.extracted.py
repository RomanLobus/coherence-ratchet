import anthropic
import json
import uuid
from datetime import datetime


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order from customer_id and items using Claude to validate and structure the data.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with keys: product_id, quantity, unit_price_cents
        
    Returns:
        Dictionary with canonical Order contract keys:
        order_id, customer_id, lines, total_cents, currency, created_at
    """
    client = anthropic.Anthropic()
    
    # Prepare the items data for Claude
    items_json = json.dumps(items, indent=2)
    
    # Use Claude to validate and structure the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are an order processing system. Given the following customer ID and items, 
create a properly structured order JSON response.

Customer ID: {customer_id}
Items (each with product_id, quantity, unit_price_cents):
{items_json}

Return ONLY a valid JSON object (no markdown, no extra text) with this exact structure:
{{
  "order_id": "<generated UUID>",
  "customer_id": "<customer_id>",
  "lines": [
    {{"product_id": "<id>", "quantity": <num>, "unit_price_cents": <num>}},
    ...
  ],
  "total_cents": <total in cents>,
  "currency": "USD",
  "created_at": "<ISO 8601 timestamp>"
}}

Calculate total_cents as the sum of (quantity * unit_price_cents) for all items.
Use current UTC time for created_at."""
            }
        ]
    )
    
    # Parse the response from Claude
    response_text = message.content[0].text.strip()
    
    # Handle markdown code blocks if present
    if response_text.startswith("
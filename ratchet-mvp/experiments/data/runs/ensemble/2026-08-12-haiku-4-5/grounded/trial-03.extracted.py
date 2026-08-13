import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with keys: product_id, quantity, unit_price_cents
    
    Returns:
        Order dictionary with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Prepare the prompt for Claude to validate and process the order
    items_description = json.dumps(items, indent=2)
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Process this order data and return a JSON response.

Customer ID: {customer_id}
Items: {items_description}

For each item, you must have: product_id, quantity, unit_price_cents
Calculate the total_cents by summing (quantity * unit_price_cents) for all items.
Use currency: "USD"
Use created_at in ISO 8601 format.

Return ONLY valid JSON (no markdown, no code blocks) with this exact structure:
{{
  "order_id": "<generated UUID>",
  "customer_id": "{customer_id}",
  "lines": [
    {{"product_id": "...", "quantity": <num>, "unit_price_cents": <num>}},
    ...
  ],
  "total_cents": <total>,
  "currency": "USD",
  "created_at": "<ISO 8601 timestamp>"
}}"""
            }
        ]
    )
    
    # Extract the response text
    response_text = message.content[0].text.strip()
    
    # Remove markdown code blocks if present
    if response_text.startswith("
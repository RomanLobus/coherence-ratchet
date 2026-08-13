import anthropic
import json
import uuid
from datetime import datetime


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dicts with product_id, quantity, unit_price_cents
    
    Returns:
        A dictionary with the canonical order structure
    """
    client = anthropic.Anthropic()
    
    # Prepare the items for Claude to validate
    items_json = json.dumps(items, indent=2)
    
    prompt = f"""You are an order validation and structuring system. 
Given the following customer ID and items, validate the data and return a JSON object with the exact canonical structure.

Customer ID: {customer_id}

Items to validate:
{items_json}

Each item should have: product_id (string), quantity (positive integer), unit_price_cents (positive integer).

Return ONLY a valid JSON object with this exact structure:
{{
  "order_id": "unique-uuid-string",
  "customer_id": "the-customer-id",
  "lines": [
    {{
      "product_id": "product-id",
      "quantity": number,
      "unit_price_cents": number
    }}
  ],
  "total_cents": number,
  "currency": "USD",
  "created_at": "ISO-8601-timestamp"
}}

Calculate total_cents as the sum of (quantity * unit_price_cents) for all lines.
Use current UTC time for created_at.
Do not include any explanatory text, only the JSON."""

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

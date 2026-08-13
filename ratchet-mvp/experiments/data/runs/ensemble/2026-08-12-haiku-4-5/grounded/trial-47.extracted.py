import anthropic
import json
import uuid
from datetime import datetime


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with keys: product_id, quantity, unit_price_cents
    
    Returns:
        A dictionary with the canonical Order contract fields
    """
    client = anthropic.Anthropic()
    
    items_json = json.dumps(items, indent=2)
    
    prompt = f"""You are an order processing system. Given the following customer and items data, 
return a valid JSON order object that conforms to this exact schema:

{{
  "order_id": "string (UUID format)",
  "customer_id": "string",
  "lines": [
    {{
      "product_id": "string",
      "quantity": "integer",
      "unit_price_cents": "integer"
    }}
  ],
  "total_cents": "integer (sum of quantity * unit_price_cents for all lines)",
  "currency": "string (always 'USD')",
  "created_at": "string (ISO 8601 timestamp)"
}}

Customer ID: {customer_id}

Items data:
{items_json}

Return ONLY the valid JSON object, no additional text or explanation."""

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


if __name__ == "__main__":
    sample_items = [
        {"product_id": "PROD-001", "quantity": 2, "unit_price_cents": 1999},
        {"product_id": "PROD-002", "quantity": 1, "unit_price_cents": 4999},
        {"product_id": "PROD-003", "quantity": 3, "unit_price_cents": 799}
    ]
    
    order = build_order("CUST-12345", sample_items)
    print(json.dumps(order, indent=2))

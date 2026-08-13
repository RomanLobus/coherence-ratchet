import anthropic
from datetime import datetime
import uuid
import json


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary with the canonical field set using Claude.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with product_id, quantity, and unit_price_cents
    
    Returns:
        A dictionary with the canonical order structure
    """
    client = anthropic.Anthropic()
    
    # Calculate total
    total_cents = sum(item["quantity"] * item["unit_price_cents"] for item in items)
    
    # Prepare items for Claude
    items_description = json.dumps(items, indent=2)
    
    prompt = f"""You are an order processing assistant. Given the following customer order details, generate a valid order in JSON format.

Customer ID: {customer_id}
Items:
{items_description}
Total: {total_cents} cents
Currency: USD

Generate a JSON response with this exact structure:
{{
  "order_id": "<a unique order id>",
  "customer_id": "{customer_id}",
  "lines": [
    {{
      "product_id": "<product_id>",
      "quantity": <quantity>,
      "unit_price_cents": <price_in_cents>
    }}
  ],
  "total_cents": {total_cents},
  "currency": "USD",
  "created_at": "<ISO 8601 timestamp>"
}}

Return only the JSON object, no other text."""
    
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
    
    # Validate the order structure
    required_keys = {"order_id", "customer_id", "lines", "total_cents", "currency", "created_at"}
    if not all(key in order for key in required_keys):
        raise ValueError(f"Order missing required keys. Expected: {required_keys}, Got: {set(order.keys())}")
    
    # Validate lines structure
    for line in order["lines"]:
        required_line_keys = {"product_id", "quantity", "unit_price_cents"}
        if not all(key in line for key in required_line_keys):
            raise ValueError(f"Line item missing required keys. Expected: {required_line_keys}, Got: {set(line.keys())}")
    
    return order


if __name__ == "__main__":
    # Example usage
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price_cents": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price_cents": 4999},
    ]
    
    order = build_order("CUST123", test_items)
    print(json.dumps(order, indent=2))

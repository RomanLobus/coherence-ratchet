import anthropic
import json
from datetime import datetime
import uuid

def build_order(customer_id, items):
    """
    Build an order dictionary using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with keys: product_id, quantity, unit_price_cents
    
    Returns:
        Dictionary with order structure: order_id, customer_id, lines, total_cents, currency, created_at
    """
    client = anthropic.Anthropic()
    
    # Prepare the items for validation
    items_json = json.dumps(items)
    
    prompt = f"""You are an order validation and construction system. 
    
Given the following items for a customer order:
{items_json}

Create a valid order with the following requirements:
1. Generate a unique order_id (use UUID format)
2. Use the provided customer_id: {customer_id}
3. Create line items with exactly these keys: product_id, quantity, unit_price_cents
4. Calculate the total_cents by summing (quantity * unit_price_cents) for all items
5. Use "USD" as the currency
6. Use the current ISO format timestamp for created_at

Return ONLY valid JSON that matches this structure (no additional text or explanation):
{{
  "order_id": "string (UUID)",
  "customer_id": "string",
  "lines": [
    {{
      "product_id": "string",
      "quantity": number,
      "unit_price_cents": number
    }}
  ],
  "total_cents": number,
  "currency": "string",
  "created_at": "string (ISO format)"
}}"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    order_dict = json.loads(response_text)
    
    return order_dict

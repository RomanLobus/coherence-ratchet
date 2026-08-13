import anthropic
import json
from typing import Any

def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', 'unit_price_cents'
    
    Returns:
        Order dictionary with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Calculate total from items
    total_cents = sum(item['quantity'] * item['unit_price_cents'] for item in items)
    
    # Create the lines array with exact keys
    lines = [
        {
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'unit_price_cents': item['unit_price_cents']
        }
        for item in items
    ]
    
    # Use Claude to validate and format the order
    prompt = f"""Given the following order details, return ONLY valid JSON in this exact format:
{{
  "order_id": "generated_id",
  "customer_id": "{customer_id}",
  "lines": {json.dumps(lines)},
  "total_cents": {total_cents},
  "currency": "USD",
  "created_at": "ISO8601_timestamp"
}}

Generate a unique order_id and current ISO8601 timestamp. Return ONLY the JSON, no other text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    # Validate that we have exactly the required fields at top level
    required_fields = {'order_id', 'customer_id', 'lines', 'total_cents', 'currency', 'created_at'}
    actual_fields = set(order.keys())
    
    if actual_fields != required_fields:
        raise ValueError(f"Order has invalid fields. Expected {required_fields}, got {actual_fields}")
    
    # Validate each line has exactly the required fields
    for line in order['lines']:
        line_fields = set(line.keys())
        required_line_fields = {'product_id', 'quantity', 'unit_price_cents'}
        if line_fields != required_line_fields:
            raise ValueError(f"Line has invalid fields. Expected {required_line_fields}, got {line_fields}")
    
    return order

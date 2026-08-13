import anthropic
import json
import uuid
from datetime import datetime


def build_order(customer_id: str, items: list) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the data.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        A dictionary representing the order with canonical fields
    """
    client = anthropic.Anthropic()
    
    prompt = f"""You are an order validation and structuring service. Given customer information and items, 
return a properly formatted order JSON.

Customer ID: {customer_id}
Items: {json.dumps(items)}

Return ONLY a valid JSON object (no markdown, no extra text) with these exact top-level keys:
- order_id: A unique UUID string
- customer_id: The provided customer ID
- lines: Array of line items, each with product_id, quantity, unit_price_cents
- total_cents: Sum of (quantity * unit_price_cents) for all lines
- currency: "USD" 
- created_at: Current ISO 8601 timestamp

Example output format:
{{"order_id": "uuid-string", "customer_id": "cust123", "lines": [{{"product_id": "prod1", "quantity": 2, "unit_price_cents": 1000}}], "total_cents": 2000, "currency": "USD", "created_at": "2024-01-15T10:30:00Z"}}"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    
    order_data = json.loads(response_text)
    
    required_keys = {"order_id", "customer_id", "lines", "total_cents", "currency", "created_at"}
    if not required_keys.issubset(set(order_data.keys())):
        raise ValueError(f"Order must contain exactly these keys: {required_keys}")
    
    if len(order_data.keys()) != len(required_keys):
        extra_keys = set(order_data.keys()) - required_keys
        raise ValueError(f"Order contains unexpected keys: {extra_keys}")
    
    for line in order_data["lines"]:
        line_keys = {"product_id", "quantity", "unit_price_cents"}
        if not line_keys.issubset(set(line.keys())):
            raise ValueError(f"Each line must contain exactly: {line_keys}")
        if len(line.keys()) != len(line_keys):
            extra_line_keys = set(line.keys()) - line_keys
            raise ValueError(f"Line contains unexpected keys: {extra_line_keys}")
    
    return order_data

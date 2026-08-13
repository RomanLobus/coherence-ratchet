import anthropic
import json
import uuid
from datetime import datetime

def build_order(customer_id, items):
    """
    Build an order using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with product_id, quantity, unit_price_cents
    
    Returns:
        A dictionary representing the order with canonical field set
    """
    client = anthropic.Anthropic()
    
    prompt = f"""You are an order validation and building system. Given customer and item information, 
    you must return a valid order object with exactly these top-level keys:
    order_id, customer_id, lines, total_cents, currency, created_at
    
    Each line item must have exactly: product_id, quantity, unit_price_cents
    
    Customer ID: {customer_id}
    Items: {json.dumps(items)}
    
    Create a valid order JSON object. Use:
    - A unique UUID for order_id
    - The provided customer_id
    - Transform items into lines array with exact field names
    - Calculate total_cents from quantity * unit_price_cents for each line
    - Use "USD" for currency
    - Use current ISO timestamp for created_at
    
    Return ONLY a valid JSON object, no other text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    
    order_data = json.loads(response_text)
    
    required_keys = {'order_id', 'customer_id', 'lines', 'total_cents', 'currency', 'created_at'}
    if not all(key in order_data for key in required_keys):
        raise ValueError(f"Order missing required keys. Expected: {required_keys}, Got: {set(order_data.keys())}")
    
    for line in order_data.get('lines', []):
        line_keys = {'product_id', 'quantity', 'unit_price_cents'}
        if not all(key in line for key in line_keys):
            raise ValueError(f"Line item missing required keys. Expected: {line_keys}, Got: {set(line.keys())}")
    
    return order_data


if __name__ == "__main__":
    test_items = [
        {"product_id": "PROD-001", "quantity": 2, "unit_price_cents": 1999},
        {"product_id": "PROD-002", "quantity": 1, "unit_price_cents": 4999}
    ]
    
    order = build_order("CUST-12345", test_items)
    print(json.dumps(order, indent=2))

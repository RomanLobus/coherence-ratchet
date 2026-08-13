import anthropic
import json
from datetime import datetime
import uuid


def build_order(customer_id: str, items: list) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID for the order
        items: List of items, each with product_id, quantity, and unit_price_cents
    
    Returns:
        A dictionary representing the order with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Calculate total cents
    total_cents = sum(item['quantity'] * item['unit_price_cents'] for item in items)
    
    # Create the lines array with the exact required fields
    lines = [
        {
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'unit_price_cents': item['unit_price_cents']
        }
        for item in items
    ]
    
    # Use Claude to validate the order structure
    prompt = f"""Given this order data, validate it follows the canonical Order contract and return it in the exact format required.

Order data:
- Customer ID: {customer_id}
- Items: {json.dumps(items)}
- Total cents: {total_cents}
- Currency: USD
- Current timestamp: {datetime.now().isoformat()}

The canonical Order contract requires exactly these top-level keys:
- order_id (string, unique identifier)
- customer_id (string)
- lines (array of line items)
- total_cents (integer)
- currency (string)
- created_at (ISO 8601 timestamp string)

Each line item must have exactly:
- product_id (string)
- quantity (integer)
- unit_price_cents (integer)

Return a valid JSON object that strictly adheres to this contract. Use a UUID for the order_id."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the response and parse it as JSON
    response_text = message.content[0].text
    
    # Try to extract JSON from the response
    try:
        # Look for JSON block in the response
        if '
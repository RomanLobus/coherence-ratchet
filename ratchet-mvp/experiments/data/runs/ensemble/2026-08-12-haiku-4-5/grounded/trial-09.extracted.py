import anthropic
import json
from datetime import datetime
import uuid


def build_order(customer_id: str, items: list) -> dict:
    """
    Build an order dictionary using Claude to validate and process the items.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dicts with keys: product_id, quantity, unit_price_cents
    
    Returns:
        Order dictionary with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Create a prompt for Claude to validate and process the order
    prompt = f"""You are an order processing system. Given the following customer order data, 
    validate it and return a properly formatted JSON order object.
    
    Customer ID: {customer_id}
    Items: {json.dumps(items)}
    
    Your response must be ONLY a valid JSON object (no other text) with this exact structure:
    {{
        "order_id": "a unique order ID",
        "customer_id": "{customer_id}",
        "lines": [
            {{
                "product_id": "product ID",
                "quantity": quantity as integer,
                "unit_price_cents": price in cents as integer
            }}
        ],
        "total_cents": total price in cents as integer,
        "currency": "USD",
        "created_at": "ISO 8601 timestamp"
    }}
    
    Calculate the total_cents by summing (quantity * unit_price_cents) for all items.
    Use current UTC time for created_at.
    Generate a unique order_id."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the JSON from Claude's response
    response_text = message.content[0].text
    
    # Parse the JSON response
    order = json.loads(response_text)
    
    return order

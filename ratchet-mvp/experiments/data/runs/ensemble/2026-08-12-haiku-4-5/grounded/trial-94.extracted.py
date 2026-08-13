import anthropic
import json
import uuid
from datetime import datetime


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the data.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with product_id, quantity, and unit_price_cents
    
    Returns:
        A dictionary representing the order with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Prepare the prompt for Claude to validate and structure the order
    items_json = json.dumps(items)
    prompt = f"""You are an order processing system. Given the following customer ID and items, 
    generate a valid order JSON object.

    Customer ID: {customer_id}
    Items (each with product_id, quantity, unit_price_cents): {items_json}

    Generate a JSON object with these EXACT fields at the top level:
    - order_id: A UUID string
    - customer_id: The provided customer ID
    - lines: Array of line items (each with product_id, quantity, unit_price_cents)
    - total_cents: Sum of (quantity * unit_price_cents) for all lines
    - currency: "USD"
    - created_at: Current ISO 8601 timestamp

    Return ONLY the JSON object, no other text."""

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
    
    # Validate the response has all required fields
    required_fields = {"order_id", "customer_id", "lines", "total_cents", "currency", "created_at"}
    if not all(field in order for field in required_fields):
        raise ValueError(f"Invalid order structure. Missing fields: {required_fields - set(order.keys())}")
    
    # Validate lines have required fields
    for line in order.get("lines", []):
        required_line_fields = {"product_id", "quantity", "unit_price_cents"}
        if not all(field in line for field in required_line_fields):
            raise ValueError(f"Invalid line item structure. Missing fields: {required_line_fields - set(line.keys())}")
    
    return order

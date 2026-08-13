import anthropic
import uuid
from datetime import datetime


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with product_id, quantity, and unit_price_cents
        
    Returns:
        A dictionary representing the order with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Create the prompt for Claude to validate and build the order
    prompt = f"""You are an order processing system. Given customer data and items, you must return a valid order JSON object.

Customer ID: {customer_id}
Items: {items}

You must return ONLY a valid JSON object (no markdown, no explanation) matching this exact structure:
{{
    "order_id": "unique-order-id",
    "customer_id": "customer-id",
    "lines": [
        {{"product_id": "product-id", "quantity": number, "unit_price_cents": number}}
    ],
    "total_cents": number,
    "currency": "USD",
    "created_at": "ISO-8601 timestamp"
}}

Rules:
- order_id must be a unique UUID-like string
- customer_id must match the provided customer ID
- lines must have exactly the keys: product_id, quantity, unit_price_cents
- total_cents must be the sum of (quantity * unit_price_cents) for all lines
- currency must be "USD"
- created_at must be current ISO-8601 timestamp

Items to process:
{items}"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    import json
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    # Validate the order structure
    required_keys = {"order_id", "customer_id", "lines", "total_cents", "currency", "created_at"}
    if not all(key in order for key in required_keys):
        raise ValueError(f"Order missing required keys. Got: {set(order.keys())}")
    
    # Validate lines structure
    for line in order["lines"]:
        required_line_keys = {"product_id", "quantity", "unit_price_cents"}
        if not all(key in line for key in required_line_keys):
            raise ValueError(f"Order line missing required keys. Got: {set(line.keys())}")
    
    # Validate customer_id matches
    if order["customer_id"] != customer_id:
        raise ValueError(f"Order customer_id {order['customer_id']} does not match provided customer_id {customer_id}")
    
    # Validate total_cents calculation
    calculated_total = sum(line["quantity"] * line["unit_price_cents"] for line in order["lines"])
    if order["total_cents"] != calculated_total:
        raise ValueError(f"Order total_cents {order['total_cents']} does not match calculated total {calculated_total}")
    
    return order


if __name__ == "__main__":
    # Test the function
    items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price_cents": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price_cents": 4999},
    ]
    
    order = build_order("CUST123", items)
    print("Generated Order:")
    import json
    print(json.dumps(order, indent=2))

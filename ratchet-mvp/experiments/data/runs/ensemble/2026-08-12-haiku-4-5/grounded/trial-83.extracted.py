import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary from customer ID and items list.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        Order dictionary with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Validate items structure
    for item in items:
        if not all(key in item for key in ['product_id', 'quantity', 'unit_price_cents']):
            raise ValueError("Each item must have 'product_id', 'quantity', and 'unit_price_cents'")
    
    # Use Claude to validate and structure the order data
    prompt = f"""You are an order validation system. Given the following customer order data, validate it and return a properly formatted JSON order object.

Customer ID: {customer_id}
Items: {json.dumps(items)}

Return ONLY a valid JSON object with these exact fields:
- order_id: (generate a unique UUID string)
- customer_id: (use the provided customer_id)
- lines: (array of items with product_id, quantity, unit_price_cents)
- total_cents: (sum of quantity * unit_price_cents for all items)
- currency: "USD"
- created_at: (current ISO 8601 timestamp)

Ensure all monetary values are in cents (integers). Return ONLY the JSON object, no other text."""

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
    
    # Validate the returned order structure
    required_fields = {'order_id', 'customer_id', 'lines', 'total_cents', 'currency', 'created_at'}
    if not required_fields.issubset(set(order.keys())):
        raise ValueError(f"Order missing required fields. Got: {set(order.keys())}")
    
    # Validate lines structure
    for line in order['lines']:
        line_fields = {'product_id', 'quantity', 'unit_price_cents'}
        if not line_fields.issubset(set(line.keys())):
            raise ValueError(f"Line item missing required fields. Got: {set(line.keys())}")
    
    return order


if __name__ == "__main__":
    # Example usage
    test_items = [
        {"product_id": "SKU-001", "quantity": 2, "unit_price_cents": 5000},
        {"product_id": "SKU-002", "quantity": 1, "unit_price_cents": 12000},
    ]
    
    order = build_order("CUST-12345", test_items)
    print(json.dumps(order, indent=2))

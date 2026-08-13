import anthropic
import json
from datetime import datetime
import uuid


def build_order(customer_id: str, items: list) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the order.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with product_id, quantity, and unit_price_cents
        
    Returns:
        A dictionary representing the order with canonical field set
    """
    
    client = anthropic.Anthropic()
    
    items_description = json.dumps(items, indent=2)
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Given the following order items, build a valid order JSON response.

Customer ID: {customer_id}

Items:
{items_description}

Please validate each item has: product_id, quantity, and unit_price_cents.
Calculate the total_cents as the sum of (quantity * unit_price_cents) for each line item.
Use the current timestamp for created_at in ISO 8601 format.
Use 'USD' for currency.
Generate a unique order_id (can be a UUID string).

Return ONLY valid JSON with this exact structure at top level:
- order_id
- customer_id  
- lines (array with product_id, quantity, unit_price_cents for each item)
- total_cents
- currency
- created_at

No markdown, no explanation, just pure JSON."""
            }
        ]
    )
    
    response_text = message.content[0].text
    
    order = json.loads(response_text)
    
    required_keys = {'order_id', 'customer_id', 'lines', 'total_cents', 'currency', 'created_at'}
    if not required_keys.issubset(order.keys()):
        missing = required_keys - set(order.keys())
        raise ValueError(f"Order missing required fields: {missing}")
    
    for line in order['lines']:
        line_keys = {'product_id', 'quantity', 'unit_price_cents'}
        if not line_keys.issubset(line.keys()):
            missing = line_keys - set(line.keys())
            raise ValueError(f"Order line missing required fields: {missing}")
    
    return order


if __name__ == "__main__":
    sample_items = [
        {"product_id": "PROD-001", "quantity": 2, "unit_price_cents": 1999},
        {"product_id": "PROD-002", "quantity": 1, "unit_price_cents": 4999},
        {"product_id": "PROD-003", "quantity": 3, "unit_price_cents": 799},
    ]
    
    order = build_order("CUST-12345", sample_items)
    print(json.dumps(order, indent=2))

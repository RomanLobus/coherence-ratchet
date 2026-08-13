import anthropic
import json
import uuid
from datetime import datetime


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an Order object from customer_id and items using Claude.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        Dictionary representing the order with canonical field set
    """
    client = anthropic.Anthropic()
    
    items_str = json.dumps(items, indent=2)
    
    prompt = f"""You are an order processing system. Given the following customer and items, 
build and return a valid Order JSON object.

Customer ID: {customer_id}

Items:
{items_str}

You must return a JSON object with EXACTLY these top-level keys:
- order_id: A unique identifier for this order (use a UUID)
- customer_id: The customer identifier provided
- lines: An array of line items
- total_cents: The total order amount in cents (integer)
- currency: The currency code (use "USD")
- created_at: ISO 8601 timestamp of order creation

Each entry in lines must have EXACTLY these keys:
- product_id: The product identifier from the items
- quantity: The quantity ordered
- unit_price_cents: The unit price in cents

Calculate the total_cents by summing (quantity * unit_price_cents) for all line items.

Return only the JSON object, no other text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    test_items = [
        {"product_id": "PROD-001", "quantity": 2, "unit_price_cents": 2999},
        {"product_id": "PROD-002", "quantity": 1, "unit_price_cents": 5999},
    ]
    
    order = build_order("CUST-123", test_items)
    print(json.dumps(order, indent=2))

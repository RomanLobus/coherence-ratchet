import anthropic
import uuid
from datetime import datetime


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary with canonical field set using Claude.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', 'unit_price_cents'
    
    Returns:
        Dictionary with canonical Order contract fields
    """
    
    client = anthropic.Anthropic()
    
    prompt = f"""You are an order processing system. Given a customer ID and a list of items, 
construct a valid order dictionary.

Customer ID: {customer_id}
Items: {items}

Return a JSON object with exactly these top-level keys:
- order_id: a unique identifier (use UUID format)
- customer_id: the provided customer ID
- lines: array of line items, each with product_id, quantity, unit_price_cents
- total_cents: sum of (quantity * unit_price_cents) for all lines
- currency: "USD"
- created_at: ISO 8601 timestamp

Return ONLY the JSON object, no other text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    import json
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    items = [
        {"product_id": "PROD-001", "quantity": 2, "unit_price_cents": 1999},
        {"product_id": "PROD-002", "quantity": 1, "unit_price_cents": 5499}
    ]
    
    order = build_order("CUST-12345", items)
    
    import json
    print(json.dumps(order, indent=2))

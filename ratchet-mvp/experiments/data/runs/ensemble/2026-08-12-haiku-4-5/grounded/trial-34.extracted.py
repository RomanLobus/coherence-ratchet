import anthropic
import json
from datetime import datetime
import uuid


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order from customer_id and items using Claude.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        An order dictionary with canonical fields
    """
    client = anthropic.Anthropic()
    
    prompt = f"""Given the following customer order data, construct a valid Order contract JSON object.

Customer ID: {customer_id}
Items: {json.dumps(items)}

Create an order with these exact top-level keys:
- order_id (generate a unique UUID)
- customer_id
- lines (array of line items)
- total_cents (sum of all line totals)
- currency (use "USD")
- created_at (current ISO 8601 timestamp)

Each line item must have exactly these keys:
- product_id
- quantity
- unit_price_cents

Return ONLY valid JSON, no other text."""

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
    sample_items = [
        {"product_id": "SKU-001", "quantity": 2, "unit_price_cents": 1999},
        {"product_id": "SKU-002", "quantity": 1, "unit_price_cents": 4999},
    ]
    
    order = build_order("CUST-12345", sample_items)
    print(json.dumps(order, indent=2))

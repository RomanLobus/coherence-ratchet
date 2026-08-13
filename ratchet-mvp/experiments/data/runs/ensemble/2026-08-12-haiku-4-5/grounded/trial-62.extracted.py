import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id, items):
    """
    Build an order dictionary from customer_id and items.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: List of dicts with keys: product_id, quantity, unit_price_cents
        
    Returns:
        A dict with canonical Order contract fields:
        order_id, customer_id, lines, total_cents, currency, created_at
    """
    client = anthropic.Anthropic()
    
    prompt = f"""You are an order builder service. Given a customer ID and list of items, build a valid order.

Customer ID: {customer_id}

Items to add to order:
{json.dumps(items, indent=2)}

Return ONLY a valid JSON object (no markdown, no explanation) with these exact top-level keys:
- order_id (string, unique identifier)
- customer_id (string)
- lines (array of objects with: product_id, quantity, unit_price_cents)
- total_cents (integer, sum of all line totals)
- currency (string, use "USD")
- created_at (string, ISO 8601 format)

The lines array should directly correspond to the input items."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    order_json = message.content[0].text
    order = json.loads(order_json)
    
    return order


if __name__ == "__main__":
    items = [
        {"product_id": "PROD-001", "quantity": 2, "unit_price_cents": 1999},
        {"product_id": "PROD-002", "quantity": 1, "unit_price_cents": 4999},
    ]
    
    order = build_order("CUST-12345", items)
    print(json.dumps(order, indent=2))

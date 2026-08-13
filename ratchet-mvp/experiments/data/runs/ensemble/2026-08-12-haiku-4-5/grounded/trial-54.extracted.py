"""
Module for building Order objects according to the canonical schema.
"""
import anthropic
import json
from datetime import datetime
import uuid


def build_order(customer_id: str, items: list) -> dict:
    """
    Build an order dictionary using Claude to validate and process the items.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with keys: product_id, quantity, unit_price_cents
    
    Returns:
        A dictionary with the canonical Order schema:
        - order_id
        - customer_id
        - lines (list of dicts with product_id, quantity, unit_price_cents)
        - total_cents
        - currency
        - created_at
    """
    client = anthropic.Anthropic()
    
    prompt = f"""You are an order processing assistant. Given a customer ID and a list of items, 
you must return a valid JSON order object.

Customer ID: {customer_id}
Items: {json.dumps(items)}

Return a JSON object with exactly these fields at the top level:
- order_id (a UUID string)
- customer_id (the provided customer ID)
- lines (list of items, each with: product_id, quantity, unit_price_cents)
- total_cents (sum of quantity * unit_price_cents for all lines)
- currency (use "USD")
- created_at (current timestamp in ISO format)

Return ONLY the JSON object, no other text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    order["order_id"] = str(uuid.uuid4())
    order["customer_id"] = customer_id
    order["currency"] = "USD"
    order["created_at"] = datetime.utcnow().isoformat() + "Z"
    
    order["lines"] = []
    total = 0
    for item in items:
        line = {
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price_cents": item["unit_price_cents"]
        }
        order["lines"].append(line)
        total += item["quantity"] * item["unit_price_cents"]
    
    order["total_cents"] = total
    
    return order


if __name__ == "__main__":
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price_cents": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price_cents": 4999}
    ]
    
    order = build_order("CUST123", test_items)
    print(json.dumps(order, indent=2))

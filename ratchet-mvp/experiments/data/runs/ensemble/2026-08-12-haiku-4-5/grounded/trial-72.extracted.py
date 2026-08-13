import anthropic
import json
import uuid
from datetime import datetime


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of items, each with product_id, quantity, and unit_price_cents
    
    Returns:
        A dictionary representing the order with the canonical field set
    """
    client = anthropic.Anthropic()
    
    prompt = f"""You are an order processing system. Given the following customer order data, return a JSON object with ONLY these top-level keys:
- order_id (generate a UUID)
- customer_id
- lines (array of line items)
- total_cents
- currency

Each line item must have ONLY these keys:
- product_id
- quantity
- unit_price_cents

Customer ID: {customer_id}
Items: {json.dumps(items)}

Return ONLY the JSON object, no other text. Ensure total_cents is the sum of (quantity * unit_price_cents) for all lines. Use "USD" as currency."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    required_top_level_keys = {"order_id", "customer_id", "lines", "total_cents", "currency"}
    if not set(order.keys()) == required_top_level_keys:
        raise ValueError(f"Order must have exactly these keys: {required_top_level_keys}")
    
    for line in order["lines"]:
        required_line_keys = {"product_id", "quantity", "unit_price_cents"}
        if not set(line.keys()) == required_line_keys:
            raise ValueError(f"Each line must have exactly these keys: {required_line_keys}")
    
    return order

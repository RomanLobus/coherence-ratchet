import anthropic
import json
from datetime import datetime
import uuid


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
    
    total_cents = sum(item.get('unit_price_cents', 0) * item.get('quantity', 0) for item in items)
    
    prompt = f"""You are an order processing system. Given the following customer order data, return a valid JSON order object.

Customer ID: {customer_id}
Items: {json.dumps(items)}
Total in cents: {total_cents}

Return ONLY valid JSON with these exact top-level keys:
- order_id (generate a UUID string)
- customer_id (use the provided customer ID)
- lines (array of line items, each with: product_id, quantity, unit_price_cents)
- total_cents (the calculated total)
- currency (use "USD")
- created_at (use current ISO timestamp)

Ensure the JSON is valid and contains no additional fields at the top level."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    
    order = json.loads(response_text)
    
    required_keys = {'order_id', 'customer_id', 'lines', 'total_cents', 'currency', 'created_at'}
    actual_keys = set(order.keys())
    if actual_keys != required_keys:
        order = {
            'order_id': order.get('order_id', str(uuid.uuid4())),
            'customer_id': order.get('customer_id', customer_id),
            'lines': order.get('lines', [{'product_id': item.get('product_id'), 'quantity': item.get('quantity'), 'unit_price_cents': item.get('unit_price_cents')} for item in items]),
            'total_cents': order.get('total_cents', total_cents),
            'currency': order.get('currency', 'USD'),
            'created_at': order.get('created_at', datetime.utcnow().isoformat() + 'Z')
        }
    
    return order

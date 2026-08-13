import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id: str, items: list) -> dict:
    """
    Build an order using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with product_id, quantity, and unit_price_cents
    
    Returns:
        A dictionary representing the order with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Calculate total from items
    total_cents = sum(item['quantity'] * item['unit_price_cents'] for item in items)
    
    # Prepare the items data for Claude to validate
    items_json = json.dumps(items, indent=2)
    
    # Use Claude to validate and structure the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Validate this order data and return a JSON response confirming it's valid.
                
Customer ID: {customer_id}
Items:
{items_json}

Total (calculated): {total_cents} cents

Return a JSON object with just one field: "valid": true or false. If there are any issues (missing fields, negative quantities/prices, etc.), return valid: false."""
            }
        ]
    )
    
    # Parse Claude's response
    response_text = message.content[0].text
    validation_result = json.loads(response_text)
    
    if not validation_result.get("valid", False):
        raise ValueError("Order validation failed")
    
    # Build the order with canonical fields
    order = {
        "order_id": str(uuid4()),
        "customer_id": customer_id,
        "lines": [
            {
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "unit_price_cents": item["unit_price_cents"]
            }
            for item in items
        ],
        "total_cents": total_cents,
        "currency": "USD",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return order

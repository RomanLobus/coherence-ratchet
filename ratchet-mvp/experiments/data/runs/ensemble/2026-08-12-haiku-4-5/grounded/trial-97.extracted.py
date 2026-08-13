import anthropic
import json
from datetime import datetime
import uuid


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', 'unit_price_cents'
    
    Returns:
        Order dict with canonical field set: order_id, customer_id, lines, 
        total_cents, currency, created_at
    """
    client = anthropic.Anthropic()
    
    # Validate input items
    for item in items:
        if not all(k in item for k in ['product_id', 'quantity', 'unit_price_cents']):
            raise ValueError(f"Item missing required fields: {item}")
    
    # Calculate total cents
    total_cents = sum(item['quantity'] * item['unit_price_cents'] for item in items)
    
    # Use Claude to validate the order structure
    prompt = f"""
    Validate this order and return a JSON response confirming it's properly structured.
    
    Customer ID: {customer_id}
    Items:
    {json.dumps(items, indent=2)}
    Total cents: {total_cents}
    
    Respond with ONLY valid JSON confirming the order is valid or describing any issues.
    """
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the response
    response_text = message.content[0].text
    
    # Build the canonical order structure
    order = {
        "order_id": str(uuid.uuid4()),
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

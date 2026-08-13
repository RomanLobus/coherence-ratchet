import anthropic
import json
from datetime import datetime
import uuid


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with keys: product_id, quantity, unit_price_cents
    
    Returns:
        A properly structured order dictionary with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Calculate total
    total_cents = sum(item.get("unit_price_cents", 0) * item.get("quantity", 0) for item in items)
    
    # Build lines with exact keys
    lines = [
        {
            "product_id": item.get("product_id"),
            "quantity": item.get("quantity"),
            "unit_price_cents": item.get("unit_price_cents")
        }
        for item in items
    ]
    
    # Create the order structure
    order = {
        "order_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "lines": lines,
        "total_cents": total_cents,
        "currency": "USD",
        "created_at": datetime.now().isoformat()
    }
    
    # Use Claude to validate the order structure
    prompt = f"""Validate this order structure and return it as valid JSON with no additional text:
{json.dumps(order)}

Verify:
1. order_id is a valid UUID string
2. customer_id is present
3. lines array has items with product_id, quantity, unit_price_cents
4. total_cents matches sum of (quantity * unit_price_cents) for all lines
5. currency is set
6. created_at is in ISO format

If validation passes, return the order as-is. If there are issues, fix them and return the corrected order."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse Claude's response
    response_text = message.content[0].text
    validated_order = json.loads(response_text)
    
    return validated_order

import uuid
from datetime import datetime, timezone
import anthropic
import json


def build_order(customer_id: str, items: list) -> dict:
    """
    Build an order using Claude to validate and structure the data.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', 'unit_price_cents'
    
    Returns:
        A dictionary representing the order with canonical field set
    """
    
    client = anthropic.Anthropic()
    
    prompt = f"""Given the following customer order data, validate it and return a properly formatted JSON order object.

Customer ID: {customer_id}
Items: {json.dumps(items)}

Return ONLY valid JSON (no markdown, no explanation) with this exact structure:
{{
    "lines": [
        {{"product_id": "string", "quantity": number, "unit_price_cents": number}},
        ...
    ],
    "total_cents": number,
    "currency": "USD"
}}

The total_cents should be the sum of (quantity * unit_price_cents) for all items.
Validate that:
- All product_ids are present and non-empty
- All quantities are positive integers
- All unit_price_cents are non-negative integers
- Currency is always "USD"

If validation fails, still return the JSON structure but with an empty lines array and total_cents of 0."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text.strip()
    
    response_data = json.loads(response_text)
    
    order_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    
    order = {
        "order_id": order_id,
        "customer_id": customer_id,
        "lines": response_data.get("lines", []),
        "total_cents": response_data.get("total_cents", 0),
        "currency": response_data.get("currency", "USD"),
        "created_at": created_at
    }
    
    return order

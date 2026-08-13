import anthropic
import uuid
from datetime import datetime


def build_order(customer_id: str, items: list[dict]) -> dict:
    """Build an order using Claude to validate and calculate totals."""
    client = anthropic.Anthropic()
    
    # Prepare the items for Claude validation
    items_text = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price_cents']} cents"
        for item in items
    ])
    
    # Use Claude to validate and process the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are an order processing system. Process this order for customer {customer_id}.

Items to order:
{items_text}

Return ONLY a valid JSON response with this exact structure:
{{
    "valid": true/false,
    "total_cents": <total amount in cents as integer>,
    "currency": "USD",
    "lines": [
        {{"product_id": "<id>", "quantity": <qty>, "unit_price_cents": <price>}},
        ...
    ]
}}

Calculate the total by summing (quantity * unit_price_cents) for each line.
If any item is invalid, set valid to false."""
            }
        ]
    )
    
    # Parse Claude's response
    response_text = message.content[0].text
    
    # Extract JSON from response
    import json
    try:
        # Find JSON in the response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx >= 0 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            processed = json.loads(json_str)
        else:
            raise ValueError("No JSON found in response")
    except json.JSONDecodeError:
        # Fallback: calculate totals manually if Claude's response is malformed
        processed = {
            "valid": True,
            "total_cents": sum(item['quantity'] * item['unit_price_cents'] for item in items),
            "currency": "USD",
            "lines": items
        }
    
    if not processed.get("valid", True):
        raise ValueError("Order validation failed")
    
    # Build the final order with required fields
    order = {
        "order_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "lines": processed.get("lines", items),
        "total_cents": processed.get("total_cents", sum(item['quantity'] * item['unit_price_cents'] for item in items)),
        "currency": processed.get("currency", "USD"),
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return order

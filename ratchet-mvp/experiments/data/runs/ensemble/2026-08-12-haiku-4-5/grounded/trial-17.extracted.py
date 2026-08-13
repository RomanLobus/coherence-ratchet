import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the data.
    
    Args:
        customer_id: The customer identifier
        items: List of dictionaries with product_id, quantity, and unit_price_cents
    
    Returns:
        A dictionary representing the order with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Prepare the items for Claude to validate
    items_str = json.dumps(items, indent=2)
    
    prompt = f"""You are an order validation system. Given these items, validate them and return a JSON response.

Items:
{items_str}

For each item, ensure it has:
- product_id (string)
- quantity (positive integer)
- unit_price_cents (non-negative integer)

Return a JSON object with:
1. "valid": boolean indicating if all items are valid
2. "lines": array of validated line items (product_id, quantity, unit_price_cents)
3. "total_cents": sum of (quantity * unit_price_cents) for all lines
4. "errors": array of error messages if invalid

Be strict about validation. If any item is missing required fields or has invalid types, include an error message."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse Claude's response
    response_text = message.content[0].text
    
    # Extract JSON from the response
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1
    if json_start >= 0 and json_end > json_start:
        json_str = response_text[json_start:json_end]
        validation_result = json.loads(json_str)
    else:
        raise ValueError("Could not parse Claude's response as JSON")
    
    if not validation_result.get("valid", False):
        errors = validation_result.get("errors", ["Unknown validation error"])
        raise ValueError(f"Item validation failed: {', '.join(errors)}")
    
    # Build the canonical order dictionary
    order = {
        "order_id": str(uuid4()),
        "customer_id": customer_id,
        "lines": validation_result.get("lines", []),
        "total_cents": validation_result.get("total_cents", 0),
        "currency": "USD",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return order

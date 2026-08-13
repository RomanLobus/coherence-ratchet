import anthropic
import json
from datetime import datetime
import uuid


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and process the items.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        A dictionary representing the order with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Create a prompt for Claude to validate and process the order items
    items_json = json.dumps(items, indent=2)
    prompt = f"""You are an order processing system. Given the following items, validate them and return a JSON response containing:
1. validated_lines: an array of line items, each with exactly these fields: product_id, quantity, unit_price_cents
2. total_cents: the sum of (quantity * unit_price_cents) for all items
3. any_errors: an array of any validation issues found (empty if valid)

Items to process:
{items_json}

Return ONLY valid JSON with these three fields."""
    
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
    try:
        # Try to find JSON in the response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            response_data = json.loads(json_str)
        else:
            raise ValueError("No JSON found in response")
    except (json.JSONDecodeError, ValueError) as e:
        # If parsing fails, create a basic response with the items as-is
        total = sum(item.get('quantity', 0) * item.get('unit_price_cents', 0) for item in items)
        response_data = {
            'validated_lines': items,
            'total_cents': total,
            'any_errors': [f"Failed to parse Claude response: {str(e)}"]
        }
    
    # Build the canonical order dictionary
    order = {
        'order_id': str(uuid.uuid4()),
        'customer_id': customer_id,
        'lines': response_data.get('validated_lines', items),
        'total_cents': response_data.get('total_cents', 0),
        'currency': 'USD',
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    return order


if __name__ == '__main__':
    # Example usage
    items = [
        {'product_id': 'PROD001', 'quantity': 2, 'unit_price_cents': 2999},
        {'product_id': 'PROD002', 'quantity': 1, 'unit_price_cents': 5999},
        {'product_id': 'PROD003', 'quantity': 3, 'unit_price_cents': 1499},
    ]
    
    order = build_order('CUST123', items)
    print(json.dumps(order, indent=2))

import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        A dictionary representing the order with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Calculate totals
    total_cents = sum(item['quantity'] * item['unit_price_cents'] for item in items)
    
    # Create the order structure
    order = {
        'order_id': str(uuid4()),
        'customer_id': customer_id,
        'lines': [
            {
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'unit_price_cents': item['unit_price_cents']
            }
            for item in items
        ],
        'total_cents': total_cents,
        'currency': 'USD',
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    # Use Claude to validate the order structure
    prompt = f"""You are an order validation system. Validate the following order and return it as valid JSON.
The order must have exactly these top-level keys: order_id, customer_id, lines, total_cents, currency, created_at
Each line item must have exactly: product_id, quantity, unit_price_cents

Order to validate:
{json.dumps(order, indent=2)}

Return ONLY the validated order as JSON, with no additional text or explanation."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    
    # Extract JSON from the response
    try:
        validated_order = json.loads(response_text)
    except json.JSONDecodeError:
        # If Claude's response isn't pure JSON, try to extract it
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            validated_order = json.loads(json_match.group())
        else:
            # Fall back to the original order if validation fails
            validated_order = order
    
    return validated_order


if __name__ == "__main__":
    # Test the function
    test_items = [
        {'product_id': 'PROD-001', 'quantity': 2, 'unit_price_cents': 1999},
        {'product_id': 'PROD-002', 'quantity': 1, 'unit_price_cents': 4999},
    ]
    
    order = build_order('CUST-12345', test_items)
    print(json.dumps(order, indent=2))

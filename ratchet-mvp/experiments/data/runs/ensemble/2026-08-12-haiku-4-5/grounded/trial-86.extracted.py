import anthropic
import json
from datetime import datetime
import uuid


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and process the order data.
    
    Args:
        customer_id: The customer identifier
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        Dictionary representing the order with canonical field set
    """
    
    client = anthropic.Anthropic()
    
    # Prepare the items for Claude
    items_text = json.dumps(items, indent=2)
    
    # Use Claude to validate and calculate the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are an order processing system. Process the following order items and return a JSON response.

Customer ID: {customer_id}

Items to process:
{items_text}

Please validate that each item has:
- product_id (string)
- quantity (positive number)
- unit_price_cents (positive number)

Then calculate the total price in cents by summing (quantity * unit_price_cents) for each item.

Return ONLY a valid JSON object with these exact keys:
{{
    "lines": [
        {{
            "product_id": "...",
            "quantity": ...,
            "unit_price_cents": ...
        }}
    ],
    "total_cents": ...
}}

If any item is invalid, still include it but mark with a note in your calculation. Calculate total from valid items only."""
            }
        ]
    )
    
    # Parse Claude's response
    response_text = message.content[0].text
    
    # Extract JSON from the response
    # Find the JSON object in the response
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}') + 1
    
    if start_idx != -1 and end_idx > start_idx:
        json_str = response_text[start_idx:end_idx]
        processed_data = json.loads(json_str)
    else:
        # If we can't find JSON, create a basic order structure
        total_cents = sum(item.get('quantity', 0) * item.get('unit_price_cents', 0) for item in items)
        processed_data = {
            'lines': items,
            'total_cents': total_cents
        }
    
    # Build the canonical order structure
    order = {
        'order_id': str(uuid.uuid4()),
        'customer_id': customer_id,
        'lines': processed_data.get('lines', items),
        'total_cents': processed_data.get('total_cents', 0),
        'currency': 'USD',
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    return order


if __name__ == "__main__":
    # Example usage
    sample_items = [
        {'product_id': 'PROD-001', 'quantity': 2, 'unit_price_cents': 1999},
        {'product_id': 'PROD-002', 'quantity': 1, 'unit_price_cents': 4999},
        {'product_id': 'PROD-003', 'quantity': 3, 'unit_price_cents': 799}
    ]
    
    order = build_order('CUST-12345', sample_items)
    print(json.dumps(order, indent=2))

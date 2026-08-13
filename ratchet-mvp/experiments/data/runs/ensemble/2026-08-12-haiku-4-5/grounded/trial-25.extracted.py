import anthropic
import json
import uuid
from datetime import datetime


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and process the items.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dicts with keys: product_id, quantity, unit_price_cents
        
    Returns:
        A dictionary representing the order with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Prepare items information for Claude to process
    items_str = json.dumps(items, indent=2)
    
    prompt = f"""You are an order processing system. Given the following items list, validate them and return a JSON object with the order structure.

Items to process:
{items_str}

Return ONLY a valid JSON object with exactly these keys at the top level:
- order_id (generate a UUID string)
- customer_id (use the provided value: {customer_id})
- lines (array of line items)
- total_cents (integer, sum of all line totals)
- currency (string, use "USD")
- created_at (ISO 8601 timestamp)

Each line item must have exactly these keys:
- product_id
- quantity
- unit_price_cents

Calculate the total as the sum of (quantity * unit_price_cents) for each line.
Return ONLY the JSON object, no other text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the JSON from Claude's response
    response_text = message.content[0].text
    
    # Parse the JSON response
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    # Example usage
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price_cents": 1500},
        {"product_id": "PROD002", "quantity": 1, "unit_price_cents": 3000},
    ]
    
    order = build_order("CUST123", test_items)
    print(json.dumps(order, indent=2))

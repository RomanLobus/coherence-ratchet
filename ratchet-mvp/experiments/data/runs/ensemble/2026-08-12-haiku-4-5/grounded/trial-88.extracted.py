import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude as an AI backbone for validation and processing.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        A dictionary representing the order with canonical fields
    """
    
    client = anthropic.Anthropic()
    
    # Prepare the items for Claude to validate and process
    items_str = json.dumps(items, indent=2)
    
    # Use Claude to validate and process the items
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are an order processing system. Given these items for an order, validate them and return a JSON response.

Items:
{items_str}

Each item must have:
- product_id (string)
- quantity (positive integer)
- unit_price_cents (non-negative integer)

Respond with ONLY valid JSON in this exact format:
{{
  "lines": [
    {{"product_id": "...", "quantity": ..., "unit_price_cents": ...}},
    ...
  ],
  "total_cents": ...
}}

Calculate the total_cents as the sum of (quantity * unit_price_cents) for all items."""
            }
        ]
    )
    
    # Parse Claude's response
    response_text = message.content[0].text
    processed_data = json.loads(response_text)
    
    # Build the order with canonical fields
    order = {
        "order_id": str(uuid4()),
        "customer_id": customer_id,
        "lines": processed_data["lines"],
        "total_cents": processed_data["total_cents"],
        "currency": "USD",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return order


if __name__ == "__main__":
    # Example usage
    sample_items = [
        {"product_id": "PROD-001", "quantity": 2, "unit_price_cents": 1999},
        {"product_id": "PROD-002", "quantity": 1, "unit_price_cents": 4999},
    ]
    
    order = build_order("CUST-12345", sample_items)
    print(json.dumps(order, indent=2))

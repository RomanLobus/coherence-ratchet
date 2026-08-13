import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and structure the data.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with product_id, quantity, unit_price_cents
        
    Returns:
        A dictionary with the canonical order structure
    """
    client = anthropic.Anthropic()
    
    # Prepare the items data for Claude
    items_str = json.dumps(items)
    
    # Use Claude to validate and structure the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Given this customer order data, validate and return a JSON response with:
1. A list of line items with product_id, quantity, unit_price_cents
2. The total in cents (sum of quantity * unit_price_cents for each line)
3. Confirm the currency is USD

Customer ID: {customer_id}
Items: {items_str}

Return ONLY valid JSON with this exact structure (no markdown, no extra text):
{{
  "lines": [
    {{"product_id": "...", "quantity": ..., "unit_price_cents": ...}},
    ...
  ],
  "total_cents": ...,
  "currency": "USD"
}}"""
            }
        ]
    )
    
    # Parse Claude's response
    response_text = message.content[0].text
    order_data = json.loads(response_text)
    
    # Build the complete order with all required canonical fields
    order = {
        "order_id": str(uuid4()),
        "customer_id": customer_id,
        "lines": order_data["lines"],
        "total_cents": order_data["total_cents"],
        "currency": order_data["currency"],
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return order


if __name__ == "__main__":
    # Example usage
    test_items = [
        {"product_id": "PROD-001", "quantity": 2, "unit_price_cents": 1999},
        {"product_id": "PROD-002", "quantity": 1, "unit_price_cents": 4999}
    ]
    
    order = build_order("CUST-12345", test_items)
    print(json.dumps(order, indent=2))

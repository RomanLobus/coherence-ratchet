import anthropic
import json

def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary from customer_id and items using Claude.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with product_id, quantity, and unit_price_cents
    
    Returns:
        An order dictionary with the canonical field set
    """
    client = anthropic.Anthropic()
    
    prompt = f"""You are an order builder assistant. Given a customer ID and a list of items, construct a valid order dictionary.

Customer ID: {customer_id}
Items: {json.dumps(items)}

Return ONLY a valid JSON object with exactly these top-level keys:
- order_id: a unique identifier (use format "ORD-" followed by 8 random characters)
- customer_id: the provided customer ID
- lines: array of line items, each with product_id, quantity, unit_price_cents
- total_cents: the sum of (quantity × unit_price_cents) for all lines
- currency: "USD" (assume USD)
- created_at: current timestamp in ISO 8601 format

Calculate the total_cents by multiplying quantity by unit_price_cents for each item and summing them.

Return only the JSON object, no additional text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    test_items = [
        {"product_id": "PROD-001", "quantity": 2, "unit_price_cents": 5000},
        {"product_id": "PROD-002", "quantity": 1, "unit_price_cents": 12000},
        {"product_id": "PROD-003", "quantity": 3, "unit_price_cents": 1500},
    ]
    
    order = build_order("CUST-12345", test_items)
    print(json.dumps(order, indent=2))

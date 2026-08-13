import anthropic
import json


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude API.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Calculate order total
    order_total = sum(item.get("quantity", 0) * item.get("unit_price", 0) for item in items)
    
    # Create the order structure
    order = {
        "customer_id": customer_id,
        "line_items": items,
        "order_total": order_total
    }
    
    # Use Claude to validate and format the order
    prompt = f"""Given the following order data, validate it and return it as a properly formatted JSON object.
The order should have:
- customer_id: the customer identifier
- line_items: array of items with product_id, quantity, and unit_price (in cents)
- order_total: total in cents (sum of quantity * unit_price for all items)

Order data: {json.dumps(order)}

Return ONLY the validated JSON object, nothing else."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    validated_order = json.loads(response_text)
    
    return validated_order


if __name__ == "__main__":
    # Example usage
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},  # $19.99 each
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},  # $49.99
    ]
    
    order = build_order("CUST123", test_items)
    print("Order:")
    print(json.dumps(order, indent=2))

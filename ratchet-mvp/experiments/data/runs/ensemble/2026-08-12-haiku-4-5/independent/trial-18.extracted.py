import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """Build an order dictionary with customer, line items, and total using Claude.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Create a prompt for Claude to process the order
    prompt = f"""You are an order processing system. Process this customer order and return a valid JSON response.

Customer ID: {customer_id}
Items to order:
{items}

Return a JSON object with these fields:
- customer_id: The customer ID
- line_items: Array of items with product_id, quantity, unit_price (in cents), and line_total (quantity * unit_price in cents)
- order_total: Total in cents (sum of all line_totals)

Return ONLY valid JSON, no other text."""
    
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
    import json
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    # Test the function
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},  # $19.99
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},  # $49.99
    ]
    
    order = build_order("CUST123", test_items)
    print("Order created:")
    print(f"Customer ID: {order['customer_id']}")
    print(f"Line Items: {order['line_items']}")
    print(f"Order Total: ${order['order_total'] / 100:.2f}")

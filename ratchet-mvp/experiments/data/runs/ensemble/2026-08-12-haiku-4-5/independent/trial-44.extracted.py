import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the order.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Create a message to Claude asking it to build the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Build an order from the following data. Return ONLY valid JSON with no additional text.

Customer ID: {customer_id}

Items:
{items}

Return a JSON object with:
- customer_id: the customer ID
- line_items: array of items with product_id, quantity, unit_price (in cents), and line_total (quantity * unit_price in cents)
- order_total: sum of all line_totals in cents

Example format:
{{"customer_id": "C123", "line_items": [{{"product_id": "P1", "quantity": 2, "unit_price": 1000, "line_total": 2000}}], "order_total": 2000}}"""
            }
        ]
    )
    
    # Extract the JSON response
    response_text = message.content[0].text
    
    # Parse the JSON response
    import json
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    # Test the function
    test_items = [
        {"product_id": "WIDGET-A", "quantity": 2, "unit_price": 1500},
        {"product_id": "GADGET-B", "quantity": 1, "unit_price": 2500},
    ]
    
    result = build_order("CUST-001", test_items)
    print("Order built successfully:")
    print(result)

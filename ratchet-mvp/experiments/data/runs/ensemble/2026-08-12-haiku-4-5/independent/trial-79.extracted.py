import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude AI.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total_cents'
    """
    client = anthropic.Anthropic()
    
    # Prepare the items information for Claude
    items_info = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price_cents']} cents"
        for item in items
    ])
    
    prompt = f"""You are an order processing system. Given the following customer order details, calculate the order total and format the response as JSON.

Customer ID: {customer_id}

Items:
{items_info}

Please calculate the total cost in cents (sum of quantity * unit_price for each item) and return a JSON object with this exact structure:
{{
    "customer_id": "{customer_id}",
    "line_items": [
        {{"product_id": "...", "quantity": ..., "unit_price_cents": ..., "total_cents": ...}},
        ...
    ],
    "order_total_cents": ...
}}

Return ONLY the JSON object, no additional text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    import json
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    # Test the function
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price_cents": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price_cents": 4999},
        {"product_id": "PROD003", "quantity": 3, "unit_price_cents": 599},
    ]
    
    order = build_order("CUST123", test_items)
    print("Built Order:")
    import json
    print(json.dumps(order, indent=2))

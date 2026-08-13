import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary with customer_id, line_items, and order_total (in cents)
    """
    client = anthropic.Anthropic()
    
    # Build the prompt with order details
    order_details = f"""
    Customer ID: {customer_id}
    Items to order:
    {items}
    """
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Process this order and return a JSON object with the following structure:
{{
    "customer_id": "<customer_id>",
    "line_items": [
        {{"product_id": "<id>", "quantity": <qty>, "unit_price": <price_cents>, "total": <line_total_cents>}},
        ...
    ],
    "order_total": <total_cents>
}}

Order details:
{order_details}

Return ONLY the JSON object, no other text."""
            }
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    
    # Extract JSON from the response
    import json
    import re
    
    # Try to find JSON object in the response
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        order = json.loads(json_match.group())
    else:
        # Fallback: try to parse the entire response
        order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    # Example usage
    items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},  # $19.99
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},  # $49.99
    ]
    
    order = build_order("CUST123", items)
    print("Order built successfully:")
    print(order)

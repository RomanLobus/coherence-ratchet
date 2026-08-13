import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude API to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with customer_id, line_items, and order_total
    """
    client = anthropic.Anthropic()
    
    # Prepare the items for validation
    items_str = "\n".join(
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: ${item['unit_price']/100:.2f}"
        for item in items
    )
    
    # Use Claude to validate and calculate the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Given the following order items, validate them and return a JSON response with the structure:
{{
    "line_items": [
        {{"product_id": "...", "quantity": ..., "unit_price": ..., "total": ...}},
        ...
    ],
    "order_total": ...
}}

Order items (unit prices are in cents):
{items_str}

Customer ID: {customer_id}

Please return ONLY valid JSON, no other text. Calculate totals in cents. The line item total should be quantity * unit_price. The order_total should be the sum of all line item totals."""
            }
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    
    # Extract JSON from response
    import json
    
    # Find JSON in response
    try:
        # Try to parse the entire response as JSON first
        order_data = json.loads(response_text)
    except json.JSONDecodeError:
        # If that fails, try to extract JSON from the response
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            order_data = json.loads(json_str)
        else:
            raise ValueError("Could not parse JSON from Claude response")
    
    # Build the final order dictionary
    order = {
        "customer_id": customer_id,
        "line_items": order_data.get("line_items", []),
        "order_total": order_data.get("order_total", 0)
    }
    
    return order

import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and process the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Prepare the items data for Claude
    items_text = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    # Use Claude to validate and calculate the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Process this customer order and return ONLY a valid JSON object with no additional text.
Customer ID: {customer_id}
Items:
{items_text}

Return a JSON object with this exact structure:
{{
    "customer_id": "{customer_id}",
    "items": [
        {{"product_id": "...", "quantity": ..., "unit_price": ..., "line_total": ...}},
        ...
    ],
    "total": ...
}}

Where:
- line_total = quantity * unit_price (in cents)
- total = sum of all line_totals (in cents)
- All monetary values are in cents (integers)"""
            }
        ]
    )
    
    # Parse the response
    import json
    response_text = message.content[0].text
    
    # Extract JSON from the response (in case there's any extra text)
    try:
        # Try direct parsing first
        order = json.loads(response_text)
    except json.JSONDecodeError:
        # If that fails, try to extract JSON from the text
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            order = json.loads(json_match.group())
        else:
            raise ValueError(f"Could not parse order from Claude response: {response_text}")
    
    return order

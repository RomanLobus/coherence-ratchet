import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary for a customer using Claude AI.
    
    Args:
        customer_id: The ID of the customer
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Prepare the items summary for Claude
    items_summary = []
    total_cents = 0
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']
        line_total = quantity * unit_price
        total_cents += line_total
        items_summary.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'line_total': line_total
        })
    
    # Use Claude to validate and format the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Given this order information, confirm it's valid and return it in JSON format.
Customer ID: {customer_id}
Items: {items_summary}
Total (in cents): {total_cents}

Return ONLY valid JSON with no additional text, with this exact structure:
{{"customer_id": "<customer_id>", "line_items": [items], "order_total": <total_in_cents>}}"""
            }
        ]
    )
    
    # Parse Claude's response
    response_text = message.content[0].text
    
    # Extract JSON from response (handle potential markdown formatting)
    import json
    
    # Try to parse directly first
    try:
        order = json.loads(response_text)
    except json.JSONDecodeError:
        # If that fails, try to extract JSON from markdown code blocks
        if '
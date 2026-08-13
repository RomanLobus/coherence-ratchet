import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to generate order details.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Calculate order total
    order_total = sum(item['quantity'] * item['unit_price'] for item in items)
    
    # Prepare line items with calculated totals
    line_items = []
    for item in items:
        line_items.append({
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'unit_price': item['unit_price'],
            'total': item['quantity'] * item['unit_price']
        })
    
    # Use Claude to enhance order with additional details
    prompt = f"""Given the following order data, provide a properly formatted JSON response that includes the customer ID, formatted line items, and order total in cents.

Customer ID: {customer_id}
Line Items: {line_items}
Order Total (cents): {order_total}

Return ONLY a valid JSON object with the structure:
{{
    "customer": "<customer_id>",
    "line_items": [<array of line items>],
    "order_total": <total in cents>
}}"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse Claude's response
    import json
    response_text = message.content[0].text
    
    # Extract JSON from response if wrapped in markdown code blocks
    if response_text.startswith("
    if response_text.endswith("
    order = json.loads(response_text.strip())
    
    return order

import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude AI.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Create a prompt for Claude to build the order
    items_str = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: ${item['unit_price']/100:.2f} (${item['unit_price']} cents)"
        for item in items
    ])
    
    prompt = f"""You are an order processing system. Process the following order and return ONLY a valid JSON object with no additional text or markdown formatting.

Customer ID: {customer_id}
Items:
{items_str}

Return a JSON object with exactly these fields:
- customer_id: the customer ID
- line_items: array of items with product_id, quantity, unit_price (in cents), and line_total (in cents)
- total: total order amount in cents (integer)

Example format:
{{"customer_id": "123", "line_items": [{{"product_id": "ABC", "quantity": 2, "unit_price": 1000, "line_total": 2000}}], "total": 2000}}

Return ONLY the JSON object, no other text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text.strip()
    
    # Remove markdown code blocks if present
    if response_text.startswith("
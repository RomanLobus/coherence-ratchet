import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude to validate and structure the data.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Create a prompt for Claude to validate and build the order
    prompt = f"""Given the following customer order data, validate it and return a properly formatted order dictionary.

Customer ID: {customer_id}
Items: {items}

Please validate that:
1. customer_id is provided
2. items is a non-empty list
3. each item has product_id, quantity (positive integer), and unit_price (positive integer in cents)

Calculate the order total by summing up (quantity * unit_price) for each item.

Return ONLY a valid Python dictionary string (no markdown, no explanation) in this exact format:
{{"customer_id": "...", "items": [...], "total": ...}}

The items in the returned dictionary should be the same as the input items list."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text.strip()
    
    # Parse the response to get the dictionary
    # Remove any markdown code blocks if present
    if response_text.startswith("
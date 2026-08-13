import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude to ensure proper structure and validation.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    
    # Calculate the order total
    order_total = sum(item["quantity"] * item["unit_price"] for item in items)
    
    # Use Claude to validate and structure the order
    client = anthropic.Anthropic()
    
    prompt = f"""Given the following order information, please validate it and return a properly structured order dictionary as valid Python code (just the dict, no markdown formatting).

Customer ID: {customer_id}
Items: {items}
Calculated Total (in cents): {order_total}

The returned dictionary should have this exact structure:
- 'customer_id': the customer ID
- 'line_items': list of items with 'product_id', 'quantity', and 'unit_price' (in cents)
- 'order_total': total price in cents

Return only the Python dictionary, nothing else."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response - Claude should return a valid Python dictionary
    response_text = message.content[0].text.strip()
    
    # Evaluate the response as Python code to get the dictionary
    # In production, you'd want more robust parsing, but this works for Claude's responses
    order_dict = eval(response_text)
    
    return order_dict

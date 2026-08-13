import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude to structure the order data.
    
    Args:
        customer_id: The customer's ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Calculate total
    total = sum(item['quantity'] * item['unit_price'] for item in items)
    
    # Use Claude to validate and structure the order
    prompt = f"""Given the following order information, return a JSON object with the order structure.

Customer ID: {customer_id}
Items: {items}
Total (in cents): {total}

Return a JSON object with:
- customer_id: the customer identifier
- line_items: array of items with product_id, quantity, and unit_price
- total: total order amount in cents

Just return the JSON object, no other text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the JSON response
    response_text = message.content[0].text
    
    # Parse the JSON response
    import json
    order = json.loads(response_text)
    
    return order

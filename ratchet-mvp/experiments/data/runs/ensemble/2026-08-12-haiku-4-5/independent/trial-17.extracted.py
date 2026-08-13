import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    prompt = f"""You are an order processing system. Process the following order data and return a valid order structure.

Customer ID: {customer_id}
Items: {items}

Please validate the items and calculate the total. Return a JSON object with:
- customer_id: the customer ID
- line_items: array of items with product_id, quantity, unit_price (in cents), and line_total (quantity * unit_price)
- order_total: sum of all line totals in cents

Return ONLY valid JSON, no other text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    import json
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order

import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude AI to ensure proper formatting and validation.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Calculate totals for reference
    order_total_cents = sum(item['quantity'] * item['unit_price'] for item in items)
    
    # Create a prompt for Claude to help structure the order
    prompt = f"""Given the following customer order information, create a properly formatted order dictionary.

Customer ID: {customer_id}
Items: {items}
Calculated Total (in cents): {order_total_cents}

Please respond with ONLY a valid Python dictionary (no markdown, no explanation) with the following structure:
{{
    "customer_id": "<customer_id>",
    "line_items": [
        {{"product_id": "<id>", "quantity": <qty>, "unit_price": <price_in_cents>, "total": <line_total_cents>}},
        ...
    ],
    "order_total": <total_in_cents>
}}

Ensure all monetary values are in cents and the order_total matches the sum of all line item totals."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text.strip()
    
    # Parse the response
    order_dict = eval(response_text)
    
    return order_dict

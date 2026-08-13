import anthropic


def build_order(customer_id, items):
    """
    Build an order using Claude to validate and structure the data.
    
    Args:
        customer_id: The customer ID for the order
        items: A list of dictionaries with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        A dictionary representing the order with customer, line_items, and total
    """
    client = anthropic.Anthropic()
    
    # Create a prompt for Claude to build and validate the order
    prompt = f"""You are an order processing system. Given a customer ID and a list of items, 
build a valid order structure and return it as a JSON object.

Customer ID: {customer_id}
Items: {items}

Please return a JSON object with the following structure:
{{
    "customer_id": <customer_id>,
    "line_items": [
        {{
            "product_id": <product_id>,
            "quantity": <quantity>,
            "unit_price_cents": <unit_price_cents>,
            "total_cents": <quantity * unit_price_cents>
        }}
    ],
    "order_total_cents": <sum of all line item totals>
}}

Return ONLY the JSON object, no additional text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    
    # Clean up the response in case there are extra spaces or newlines
    response_text = response_text.strip()
    
    # Handle potential markdown code blocks
    if response_text.startswith('
    if response_text.endswith('
    response_text = response_text.strip()
    
    # Parse JSON
    import json
    order = json.loads(response_text)
    
    return order

import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude AI.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with customer_id, line_items, and order_total
    """
    client = anthropic.Anthropic()
    
    # Calculate the order total
    total_cents = sum(item['quantity'] * item['unit_price'] for item in items)
    
    # Create the prompt for Claude
    prompt = f"""You are an order processing assistant. Given the following order details, return a properly formatted order dictionary.

Customer ID: {customer_id}
Items:
{chr(10).join(f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: ${item['unit_price']/100:.2f}" for item in items)}

Total Order Amount: ${total_cents/100:.2f}

Please return the order as a JSON dictionary with the following structure:
{{
    "customer_id": "<customer_id>",
    "line_items": [
        {{
            "product_id": "<product_id>",
            "quantity": <quantity>,
            "unit_price": <unit_price_in_cents>,
            "subtotal": <subtotal_in_cents>
        }}
    ],
    "order_total": <total_in_cents>
}}

Return ONLY the JSON dictionary, no other text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    
    # Try to extract JSON from the response
    import json
    try:
        order = json.loads(response_text)
    except json.JSONDecodeError:
        # If Claude's response contains markdown code blocks, extract the JSON
        if '
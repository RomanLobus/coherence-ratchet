import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary with customer_id, line_items, and order_total (in cents)
    """
    client = anthropic.Anthropic()
    
    prompt = f"""Given the following customer order data, please validate it and return a properly structured order in JSON format.

Customer ID: {customer_id}
Items: {items}

Please return a JSON object with the following structure:
{{
    "customer_id": "the customer id",
    "line_items": [
        {{
            "product_id": "product id",
            "quantity": quantity,
            "unit_price": unit price in cents,
            "subtotal": quantity * unit_price in cents
        }}
    ],
    "order_total": total amount in cents
}}

Return ONLY valid JSON, no markdown formatting or additional text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    import json
    response_text = message.content[0].text.strip()
    order_data = json.loads(response_text)
    
    return order_data

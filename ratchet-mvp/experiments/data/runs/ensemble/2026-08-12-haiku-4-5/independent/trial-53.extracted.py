import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Prepare the items for the prompt
    items_text = "\n".join(
        f"- Product ID: {item.get('product_id')}, Quantity: {item.get('quantity')}, Unit Price: {item.get('unit_price')} cents"
        for item in items
    )
    
    prompt = f"""You are an order processing system. Given the following order information, calculate the order total and format the response as a JSON object.

Customer ID: {customer_id}
Items:
{items_text}

Please respond with ONLY a valid JSON object (no markdown, no extra text) with this exact structure:
{{
    "customer_id": "{customer_id}",
    "line_items": [
        {{"product_id": "...", "quantity": ..., "unit_price": ..., "line_total": ...}},
        ...
    ],
    "order_total": ...
}}

Where all prices are in cents and order_total is the sum of all line_totals."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text.strip()
    
    # If response is wrapped in markdown code blocks, extract the JSON
    if response_text.startswith("
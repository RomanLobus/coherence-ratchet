import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude AI.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Prepare the items summary for Claude
    items_summary = []
    for item in items:
        items_summary.append(
            f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, "
            f"Unit Price: {item['unit_price']} cents"
        )
    
    prompt = f"""You are an order processing system. Build a complete order for the following:

Customer ID: {customer_id}

Items:
{chr(10).join(items_summary)}

Please return ONLY a valid JSON object (no markdown, no code blocks) with this exact structure:
{{
    "customer_id": "{customer_id}",
    "line_items": [
        {{"product_id": "...", "quantity": ..., "unit_price": ..., "subtotal": ...}},
        ...
    ],
    "total": ...
}}

Where:
- Each line_item has product_id, quantity, unit_price (in cents), and subtotal (quantity * unit_price in cents)
- total is the sum of all line_item subtotals in cents

Return only the JSON object, nothing else."""

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

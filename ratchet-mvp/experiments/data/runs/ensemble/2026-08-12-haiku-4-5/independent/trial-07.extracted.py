import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude API.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary representing the order with customer, line_items, and total
    """
    client = anthropic.Anthropic()
    
    # Create the prompt for Claude
    items_text = "\n".join([
        f"  - Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    prompt = f"""You are an order processing system. Build an order for the following:

Customer ID: {customer_id}
Items:
{items_text}

Return ONLY a valid JSON object (no markdown, no code blocks, no extra text) with this exact structure:
{{
  "customer_id": "{customer_id}",
  "line_items": [
    {{"product_id": "...", "quantity": ..., "unit_price": ..., "line_total": ...}},
    ...
  ],
  "order_total": ...
}}

For each line item, calculate the line_total as quantity * unit_price.
The order_total should be the sum of all line_totals.
All prices should remain in cents."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    import json
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order

import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary for a customer using Claude.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    items_description = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    prompt = f"""You are an order processing system. Build an order for the following:

Customer ID: {customer_id}
Items:
{items_description}

For each item, calculate the line total (quantity × unit_price).
Calculate the order total (sum of all line totals).

Return a JSON object with this structure:
{{
    "customer_id": "<customer_id>",
    "items": [
        {{
            "product_id": "<product_id>",
            "quantity": <quantity>,
            "unit_price": <unit_price_in_cents>,
            "line_total": <line_total_in_cents>
        }}
    ],
    "total": <total_in_cents>
}}

Only return the JSON object, no other text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    
    import json
    order = json.loads(response_text)
    
    return order

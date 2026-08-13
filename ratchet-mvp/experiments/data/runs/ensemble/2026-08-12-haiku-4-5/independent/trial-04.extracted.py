import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary for a customer.
    
    Args:
        customer_id: The customer identifier
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Format the items for the AI to process
    items_str = "\n".join(
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: ${item['unit_price']/100:.2f}"
        for item in items
    )
    
    prompt = f"""Calculate the total cost of this order. For each line item, multiply quantity by unit price.

Customer ID: {customer_id}

Line Items:
{items_str}

Return ONLY a JSON object with this exact structure:
{{
    "customer_id": "{customer_id}",
    "line_items": [
        {{"product_id": "...", "quantity": ..., "unit_price": ..., "line_total": ...}},
        ...
    ],
    "order_total": ...
}}

All prices should be in cents (integers). Do not include any text outside the JSON."""
    
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

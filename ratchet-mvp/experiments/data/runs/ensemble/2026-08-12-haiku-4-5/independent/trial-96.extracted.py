import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude API.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    
    client = anthropic.Anthropic()
    
    items_description = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    prompt = f"""Given the following order items, calculate the line item totals and order total, then return ONLY a valid JSON object (no markdown, no code blocks, no extra text).

Customer ID: {customer_id}

Items:
{items_description}

For each item, calculate: quantity × unit_price (in cents)

Return a JSON object with this exact structure:
{{
    "customer_id": "{customer_id}",
    "line_items": [
        {{"product_id": "...", "quantity": ..., "unit_price": ..., "total": ...}},
        ...
    ],
    "order_total": ...
}}

All prices should be in cents as integers."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    import json
    order = json.loads(message.content[0].text)
    
    return order


if __name__ == "__main__":
    sample_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},
        {"product_id": "PROD003", "quantity": 3, "unit_price": 799},
    ]
    
    order = build_order("CUST123", sample_items)
    print("Order:")
    import json
    print(json.dumps(order, indent=2))

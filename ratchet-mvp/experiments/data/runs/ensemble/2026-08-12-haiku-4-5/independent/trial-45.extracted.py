import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Prepare the items information for Claude
    items_str = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    # Use Claude to calculate order total and format the response
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Given the following order items, create a JSON response with the order details.

Customer ID: {customer_id}
Items:
{items_str}

Please return a JSON object with:
1. "customer_id": the customer ID
2. "line_items": array of items with product_id, quantity, unit_price (in cents), and line_total (quantity * unit_price in cents)
3. "order_total": sum of all line_totals in cents

Return ONLY valid JSON, no other text."""
            }
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    
    # Extract JSON from the response (in case there's any extra text)
    import json
    import re
    
    # Try to find JSON in the response
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        order = json.loads(json_match.group())
    else:
        order = json.loads(response_text)
    
    return order

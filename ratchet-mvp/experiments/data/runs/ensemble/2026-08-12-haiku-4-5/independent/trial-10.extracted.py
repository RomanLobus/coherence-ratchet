import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude to calculate totals and format the order.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Calculate line item totals
    line_items = []
    total_cents = 0
    
    for item in items:
        line_total = item['quantity'] * item['unit_price']
        total_cents += line_total
        line_items.append({
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'unit_price': item['unit_price'],
            'line_total': line_total
        })
    
    # Use Claude to validate and format the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Validate this order data and respond with ONLY a Python dictionary (no other text).
The response must be valid Python syntax that can be evaluated.

Order data:
- Customer ID: {customer_id}
- Line items: {line_items}
- Total: {total_cents} cents

Return a dict with keys: customer_id, line_items, order_total"""
            }
        ]
    )
    
    # Extract the response text
    response_text = message.content[0].text.strip()
    
    # Parse the response as a Python dictionary
    order = eval(response_text)
    
    return order

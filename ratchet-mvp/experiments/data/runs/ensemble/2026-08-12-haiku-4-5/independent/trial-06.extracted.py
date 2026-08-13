import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude to process the order details.
    
    Args:
        customer_id: The customer identifier
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Calculate line item totals and validate input
    processed_items = []
    total_cents = 0
    
    for item in items:
        line_total = item['quantity'] * item['unit_price']
        total_cents += line_total
        processed_items.append({
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'unit_price': item['unit_price'],
            'line_total': line_total
        })
    
    # Use Claude to structure and validate the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Please validate and structure this order data. Return a JSON response with:
- customer_id: {customer_id}
- items: {processed_items}
- total (in cents): {total_cents}

Confirm the order structure is correct and return it as valid JSON."""
            }
        ]
    )
    
    # Parse Claude's response to ensure proper formatting
    response_text = message.content[0].text
    
    # Extract JSON from Claude's response
    import json
    
    # Try to find JSON in the response
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}') + 1
    
    if start_idx != -1 and end_idx > start_idx:
        json_str = response_text[start_idx:end_idx]
        order_data = json.loads(json_str)
    else:
        # If Claude didn't return JSON, build it ourselves
        order_data = {
            'customer_id': customer_id,
            'items': processed_items,
            'total': total_cents
        }
    
    return order_data

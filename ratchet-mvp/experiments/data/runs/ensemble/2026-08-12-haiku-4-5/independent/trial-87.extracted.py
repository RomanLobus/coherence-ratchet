import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary for a customer.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Calculate order total
    order_total = sum(item['quantity'] * item['unit_price'] for item in items)
    
    # Prepare the order data
    order_data = {
        'customer_id': customer_id,
        'line_items': items,
        'order_total': order_total
    }
    
    # Use Claude to validate and potentially enhance the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Validate this order and return it as a JSON object. 
The order has:
- customer_id: {customer_id}
- line_items: {items}
- order_total: {order_total} cents

Please verify the total is correct and return the order as valid JSON with these exact fields:
{{"customer_id": <customer_id>, "line_items": <items_array>, "order_total": <total_in_cents>}}

Return ONLY the JSON, no other text."""
            }
        ]
    )
    
    # Parse the response and return the order
    response_text = message.content[0].text
    
    # Try to extract JSON from the response
    import json
    try:
        # Look for JSON object in the response
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            validated_order = json.loads(json_str)
            return validated_order
    except (json.JSONDecodeError, ValueError):
        pass
    
    # If Claude's response couldn't be parsed, return the original order
    return order_data

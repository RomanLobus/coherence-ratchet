import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary containing customer info, line items, and total.
    
    Args:
        customer_id: The customer identifier
        items: A list of dictionaries each with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary with 'customer', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Calculate line item totals and total order amount
    line_items = []
    total_cents = 0
    
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 0)
        unit_price = item.get('unit_price', 0)
        
        line_total = quantity * unit_price
        total_cents += line_total
        
        line_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'line_total': line_total
        })
    
    # Use Claude to validate and enhance the order structure
    prompt = f"""Given the following order data, validate it and return a properly formatted order JSON.
The order should have:
- customer: the customer ID
- items: array of line items with product_id, quantity, unit_price, and line_total (all in cents)
- total: the total order amount in cents

Order data:
Customer ID: {customer_id}
Items: {line_items}
Total: {total_cents} cents

Please validate this order and return ONLY a valid JSON object with no additional text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response to get the validated order
    response_text = message.content[0].text
    
    # Extract JSON from response (in case there's any surrounding text)
    import json
    import re
    
    # Try to find JSON in the response
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            order = json.loads(json_match.group())
            return order
        except json.JSONDecodeError:
            pass
    
    # If Claude validation fails, return our constructed order
    return {
        'customer': customer_id,
        'items': line_items,
        'total': total_cents
    }

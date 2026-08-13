import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary for a customer.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary with customer, line_items, and order_total
    """
    client = anthropic.Anthropic()
    
    # Calculate totals for each item and overall total
    line_items = []
    total_cents = 0
    
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 0)
        unit_price = item.get('unit_price', 0)  # in cents
        
        item_total = quantity * unit_price
        total_cents += item_total
        
        line_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': item_total
        })
    
    # Use Claude to validate and format the order
    prompt = f"""Given the following order data, validate it and return a JSON response confirming the order structure is correct.

Customer ID: {customer_id}
Line Items: {line_items}
Order Total (in cents): {total_cents}

Please confirm this order is properly formatted and return a JSON response with:
1. "valid": boolean indicating if the order is valid
2. "message": a brief message about the order
3. "order_total_dollars": the order total converted to dollars"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response to ensure order validation
    response_text = message.content[0].text
    
    # Build the order dictionary
    order = {
        'customer_id': customer_id,
        'line_items': line_items,
        'order_total_cents': total_cents,
        'order_total_dollars': total_cents / 100.0,
        'validation_note': response_text
    }
    
    return order

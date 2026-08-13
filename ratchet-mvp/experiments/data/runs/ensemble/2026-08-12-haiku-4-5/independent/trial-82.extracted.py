import anthropic


def build_order(customer_id, items):
    """
    Build an order using Claude to process and structure the order data.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary representing the order with customer, line items, and total
    """
    client = anthropic.Anthropic()
    
    # Calculate totals for each item and overall total
    line_items = []
    total_cents = 0
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price = item['unit_price']
        item_total = quantity * unit_price
        total_cents += item_total
        
        line_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': item_total
        })
    
    # Use Claude to validate and structure the order
    prompt = f"""Given the following order information, validate it and return a properly formatted order.
Customer ID: {customer_id}
Line Items: {line_items}
Total (in cents): {total_cents}

Please confirm this order structure is valid and return a JSON representation of the order with:
- customer_id
- line_items (each with product_id, quantity, unit_price in cents, and total in cents)
- total (in cents)

Return only valid JSON, no additional text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    
    # Extract JSON from the response
    import json
    try:
        # Try to parse the response directly as JSON
        order = json.loads(response_text)
    except json.JSONDecodeError:
        # If that fails, construct the order manually
        order = {
            'customer_id': customer_id,
            'line_items': line_items,
            'total': total_cents
        }
    
    return order


if __name__ == "__main__":
    # Example usage
    test_items = [
        {'product_id': 'PROD001', 'quantity': 2, 'unit_price': 1999},
        {'product_id': 'PROD002', 'quantity': 1, 'unit_price': 4999},
        {'product_id': 'PROD003', 'quantity': 3, 'unit_price': 599}
    ]
    
    order = build_order('CUST123', test_items)
    print("Order created:")
    import json
    print(json.dumps(order, indent=2))

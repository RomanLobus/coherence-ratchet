import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude to structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary representing the order with customer, line_items, and total
    """
    client = anthropic.Anthropic()
    
    # Calculate line totals and overall total
    line_items = []
    total_cents = 0
    
    for item in items:
        line_total = item['quantity'] * item['unit_price']
        line_items.append({
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'unit_price': item['unit_price'],
            'line_total': line_total
        })
        total_cents += line_total
    
    # Use Claude to structure the order
    prompt = f"""Create a well-structured order JSON object with the following information:
    - Customer ID: {customer_id}
    - Line items: {line_items}
    - Total in cents: {total_cents}
    
    The order should have a 'customer_id' field, a 'line_items' array, and a 'total_cents' field.
    Return ONLY valid JSON, no additional text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    import json
    response_text = message.content[0].text
    order = json.loads(response_text)
    return order


if __name__ == "__main__":
    # Example usage
    items = [
        {'product_id': 'PROD001', 'quantity': 2, 'unit_price': 1000},
        {'product_id': 'PROD002', 'quantity': 1, 'unit_price': 2500}
    ]
    
    order = build_order('CUST123', items)
    print("Order created:")
    print(f"Customer ID: {order.get('customer_id')}")
    print(f"Line Items: {order.get('line_items')}")
    print(f"Total (cents): {order.get('total_cents')}")

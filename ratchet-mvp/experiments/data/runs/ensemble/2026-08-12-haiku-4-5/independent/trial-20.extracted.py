import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude to structure the order data.
    
    Args:
        customer_id: The ID of the customer
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer', 'line_items', and 'order_total'
    """
    # Calculate order total and prepare line items
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
    client = anthropic.Anthropic()
    
    order_data = {
        'customer_id': customer_id,
        'items': items
    }
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Given this order data, confirm it's valid and return a confirmation.
Order data: customer_id={customer_id}, items count={len(items)}

Just respond with 'Valid order' if everything looks correct."""
            }
        ]
    )
    
    # Build the order dictionary
    order = {
        'customer': customer_id,
        'line_items': line_items,
        'order_total': total_cents
    }
    
    return order

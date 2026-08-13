import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude to process and validate the order.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Calculate total
    total = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in items)
    
    # Prepare the order data for Claude to validate and structure
    order_data = {
        'customer_id': customer_id,
        'items': items,
        'total': total
    }
    
    # Use Claude to validate the order structure
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Validate this order and confirm it's properly structured. 
Order data: {order_data}

Please confirm:
1. Customer ID is present
2. Each item has product_id, quantity, and unit_price
3. Total is correctly calculated as sum of (quantity * unit_price) for all items

Respond with 'VALID' if everything is correct, or describe any issues."""
            }
        ]
    )
    
    # Check Claude's validation
    validation_response = message.content[0].text
    if "VALID" not in validation_response:
        raise ValueError(f"Order validation failed: {validation_response}")
    
    return order_data

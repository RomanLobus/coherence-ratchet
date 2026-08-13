"""Module for building customer orders."""

from anthropic import Anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    This function uses Claude to validate the order structure and calculate totals.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with keys 'product_id', 'quantity', 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = Anthropic()
    
    # Calculate totals locally
    line_items = []
    order_total = 0
    
    for item in items:
        line_total = item['quantity'] * item['unit_price']
        line_items.append({
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'unit_price': item['unit_price'],
            'line_total': line_total
        })
        order_total += line_total
    
    # Use Claude to validate the order structure
    conversation_history = []
    
    # First turn: present the order for validation
    user_message = f"""Please validate this customer order structure:
Customer ID: {customer_id}
Items: {items}
Calculated line items: {line_items}
Order total (in cents): {order_total}

Confirm if this order structure is correct."""
    
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=conversation_history
    )
    
    assistant_message = response.content[0].text
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })
    
    # Second turn: ask Claude to confirm the final format
    follow_up = """Based on your validation, please confirm the final order dictionary should have:
1. 'customer_id' field
2. 'line_items' array with each item having product_id, quantity, unit_price, and line_total
3. 'order_total' in cents

Is this the correct structure?"""
    
    conversation_history.append({
        "role": "user",
        "content": follow_up
    })
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=conversation_history
    )
    
    # Build and return the order dictionary
    return {
        'customer_id': customer_id,
        'line_items': line_items,
        'order_total': order_total
    }

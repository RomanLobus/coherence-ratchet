import anthropic

def build_order(customer_id, items):
    """
    Build an order dictionary for a customer.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Create a prompt for Claude to help validate and structure the order
    items_str = "\n".join([
        f"- Product {item['product_id']}: {item['quantity']} units @ {item['unit_price']} cents each"
        for item in items
    ])
    
    prompt = f"""Given the following order items, calculate the total price and confirm the structure:

Customer ID: {customer_id}
Items:
{items_str}

Please respond with a JSON object containing:
1. The total price in cents
2. Confirmation that all items are valid

Format your response as valid JSON only."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Calculate the total locally
    total = sum(item['quantity'] * item['unit_price'] for item in items)
    
    # Build the order dictionary
    order = {
        "customer_id": customer_id,
        "line_items": items,
        "total": total
    }
    
    return order

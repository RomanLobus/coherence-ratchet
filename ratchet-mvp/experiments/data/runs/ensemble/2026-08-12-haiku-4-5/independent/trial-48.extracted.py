import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude to structure the order data.
    
    Args:
        customer_id: The customer ID
        items: A list of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Calculate the total price
    total_cents = sum(item['quantity'] * item['unit_price'] for item in items)
    
    # Create a prompt for Claude to structure the order
    items_str = "\n".join([
        f"- Product {item['product_id']}: {item['quantity']} units @ {item['unit_price']} cents each = {item['quantity'] * item['unit_price']} cents"
        for item in items
    ])
    
    prompt = f"""Create an order object with the following information:
Customer ID: {customer_id}
Items:
{items_str}
Total: {total_cents} cents

Return the order as a valid JSON object with keys: customer_id, items (as a list), and total (in cents).
Each item should have: product_id, quantity, unit_price, and subtotal.
Only return the JSON object, no additional text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    import json
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    # Ensure the order has the correct structure
    if 'customer_id' not in order:
        order['customer_id'] = customer_id
    if 'total' not in order:
        order['total'] = total_cents
    if 'items' not in order:
        order['items'] = items
    
    return order

import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary for a customer using Claude API.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    
    client = anthropic.Anthropic()
    
    items_description = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are an order processing system. Build an order for the following:

Customer ID: {customer_id}

Items:
{items_description}

Calculate the order total (sum of quantity * unit_price for each item, all in cents).

Return a JSON object with:
- customer_id: the customer ID
- line_items: array of line items with product_id, quantity, unit_price (cents), and line_total (cents)
- order_total: total order amount in cents

Return ONLY valid JSON, no other text."""
            }
        ]
    )
    
    response_text = message.content[0].text
    
    import json
    order = json.loads(response_text)
    
    return order

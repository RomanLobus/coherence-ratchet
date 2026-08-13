import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude AI to structure the order data.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Calculate the total
    total = sum(item['quantity'] * item['unit_price'] for item in items)
    
    # Use Claude to validate and structure the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are an order processing assistant. Given the following order data, 
validate it and return a properly structured order. Return ONLY valid JSON with no additional text.

Customer ID: {customer_id}
Items: {items}
Calculated Total (cents): {total}

Return a JSON object with:
- customer_id: the customer ID
- items: the items list with product_id, quantity, and unit_price (all in cents for prices)
- total: the order total in cents

Ensure all prices and totals are in cents as integers."""
            }
        ]
    )
    
    # Parse the response
    import json
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order

import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary with customer info, line items, and total.
    
    Args:
        customer_id: The customer identifier
        items: List of dictionaries with keys 'product_id', 'quantity', 'unit_price' (in cents)
    
    Returns:
        Dictionary with keys 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Prepare the items for Claude
    items_str = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    # Use Claude to calculate the order total
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Calculate the total price for the following order items in cents:

{items_str}

Return ONLY a JSON object with a single key "total" containing the total price in cents as an integer. 
Example format: {{"total": 5000}}"""
            }
        ]
    )
    
    # Extract the total from Claude's response
    response_text = message.content[0].text
    # Parse the JSON response
    import json
    response_data = json.loads(response_text)
    total = response_data["total"]
    
    # Build the order dictionary
    order = {
        "customer_id": customer_id,
        "items": items,
        "total": total
    }
    
    return order

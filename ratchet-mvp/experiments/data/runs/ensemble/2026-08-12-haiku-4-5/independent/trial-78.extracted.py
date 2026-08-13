import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items list.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Use Claude to validate and process the order
    prompt = f"""Process this order and return a JSON object with the following structure:
{{"customer_id": "<customer_id>", "items": [list of items with product_id, quantity, unit_price_cents, and line_total_cents], "total_cents": <total>}}

Customer ID: {customer_id}
Items: {items}

For each item, calculate the line total (quantity * unit_price).
Calculate the order total as the sum of all line totals.
Return ONLY the JSON object, no other text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    
    # Parse the JSON response
    import json
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    # Example usage
    items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1000},  # $10.00
        {"product_id": "PROD002", "quantity": 1, "unit_price": 2500},  # $25.00
    ]
    
    order = build_order("CUST123", items)
    print(order)

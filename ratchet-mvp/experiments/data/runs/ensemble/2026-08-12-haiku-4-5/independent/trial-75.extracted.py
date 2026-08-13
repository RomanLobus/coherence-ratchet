import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items list.
    
    Args:
        customer_id: The ID of the customer
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    prompt = f"""You are an order processing system. Given the following order information, 
    return a valid JSON object with the order details.
    
    Customer ID: {customer_id}
    Items: {items}
    
    The JSON should have this structure:
    {{
        "customer_id": <customer_id>,
        "items": [
            {{
                "product_id": <product_id>,
                "quantity": <quantity>,
                "unit_price": <unit_price in cents>,
                "line_total": <quantity * unit_price in cents>
            }}
        ],
        "total": <sum of all line totals in cents>
    }}
    
    Return ONLY the JSON object, no other text."""
    
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
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},
    ]
    
    order = build_order("CUST123", test_items)
    print("Order built successfully:")
    import json
    print(json.dumps(order, indent=2))

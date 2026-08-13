import anthropic


def build_order(customer_id, items):
    """
    Build an order using Claude to calculate totals and structure the order.
    
    Args:
        customer_id: The customer's ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary representing the order with customer, line_items, and order_total
    """
    client = anthropic.Anthropic()
    
    # Format items for Claude
    items_str = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    prompt = f"""Calculate the total for this order and return the result as a JSON object.

Customer ID: {customer_id}
Items:
{items_str}

Please return a JSON object with this exact structure:
{{
    "customer_id": <customer_id>,
    "line_items": [
        {{
            "product_id": <product_id>,
            "quantity": <quantity>,
            "unit_price": <unit_price>,
            "total": <quantity * unit_price>
        }}
    ],
    "order_total": <sum of all line item totals>
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
    result = json.loads(message.content[0].text)
    return result


if __name__ == "__main__":
    # Test the function
    test_order = build_order("CUST123", [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 999},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 2500},
        {"product_id": "PROD003", "quantity": 3, "unit_price": 450}
    ])
    
    import json
    print(json.dumps(test_order, indent=2))

import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and process the order.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary containing customer_id, items, and total (in cents)
    """
    client = anthropic.Anthropic()
    
    items_str = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    prompt = f"""You are an order processing system. Process the following order and return a JSON response.

Customer ID: {customer_id}

Items:
{items_str}

Calculate the total cost in cents (quantity × unit_price for each item, then sum).

Return ONLY valid JSON with this exact structure:
{{
    "customer_id": "{customer_id}",
    "items": [
        {{"product_id": "...", "quantity": ..., "unit_price": ..., "line_total": ...}},
        ...
    ],
    "total": ...
}}

Where line_total is quantity × unit_price for each item, and total is the sum of all line_totals."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    import json
    response_text = message.content[0].text
    order_dict = json.loads(response_text)
    
    return order_dict


if __name__ == "__main__":
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},
        {"product_id": "PROD003", "quantity": 3, "unit_price": 799}
    ]
    
    order = build_order("CUST12345", test_items)
    print("Order:")
    print(f"Customer ID: {order['customer_id']}")
    print("Items:")
    for item in order['items']:
        print(f"  - Product: {item['product_id']}, Qty: {item['quantity']}, Unit Price: {item['unit_price']} cents, Line Total: {item['line_total']} cents")
    print(f"Total: {order['total']} cents (${order['total']/100:.2f})")

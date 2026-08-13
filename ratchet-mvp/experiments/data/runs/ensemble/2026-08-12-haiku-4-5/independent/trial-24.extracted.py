import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    items_str = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    prompt = f"""You are an order processing system. Process this order and return a JSON response.

Customer ID: {customer_id}
Items:
{items_str}

Return a JSON object with:
1. "customer_id": the customer ID
2. "items": array of items with product_id, quantity, unit_price (in cents), and line_total (quantity * unit_price in cents)
3. "total": total order amount in cents (sum of all line totals)

Return ONLY valid JSON, no other text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    
    import json
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},
        {"product_id": "PROD003", "quantity": 3, "unit_price": 799},
    ]
    
    order = build_order("CUST123", test_items)
    print("Order built successfully:")
    print(order)

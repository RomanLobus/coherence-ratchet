import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the order.

    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)

    Returns:
        Dictionary representing the order with customer, line_items, and total
    """
    client = anthropic.Anthropic()

    # Prepare the items for Claude to process
    items_str = "\n".join(
        [
            f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
            for item in items
        ]
    )

    prompt = f"""
    I need to build an order. Please process this order data and return a JSON response.
    
    Customer ID: {customer_id}
    Items:
    {items_str}
    
    Please return a JSON object with:
    1. "customer_id": the customer ID
    2. "line_items": an array of line items, each with "product_id", "quantity", "unit_price", and "line_total" (quantity * unit_price in cents)
    3. "total": the total order amount in cents (sum of all line totals)
    
    Return ONLY the JSON object, no other text.
    """

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text

    import json

    order = json.loads(response_text)

    return order


if __name__ == "__main__":
    # Example usage
    items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},
        {"product_id": "PROD003", "quantity": 3, "unit_price": 799},
    ]

    order = build_order("CUST123", items)
    print("Order:")
    import json

    print(json.dumps(order, indent=2))

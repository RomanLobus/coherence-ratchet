import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude AI to validate and structure the order.

    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)

    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()

    items_str = "\n".join(
        [
            f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: ${item['unit_price']/100:.2f} ({item['unit_price']} cents)"
            for item in items
        ]
    )

    prompt = f"""Process this customer order:
Customer ID: {customer_id}
Items:
{items_str}

Return a JSON response with:
1. customer_id (string)
2. line_items (array of objects with product_id, quantity, unit_price in cents, and line_total in cents)
3. order_total (integer in cents)

Validate that all quantities are positive and prices are positive. Calculate line totals and order total correctly.
Return ONLY valid JSON, no other text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    import json

    response_text = message.content[0].text
    order = json.loads(response_text)

    return order


if __name__ == "__main__":
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},
        {"product_id": "PROD003", "quantity": 3, "unit_price": 799},
    ]

    order = build_order("CUST123", test_items)
    print("Order Result:")
    print(f"Customer ID: {order['customer_id']}")
    print(f"Line Items: {order['line_items']}")
    print(f"Order Total: ${order['order_total']/100:.2f} ({order['order_total']} cents)")

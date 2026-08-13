import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and process the order.

    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)

    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()

    # Prepare the items for Claude
    items_text = ""
    for i, item in enumerate(items, 1):
        items_text += f"\nItem {i}: Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"

    prompt = f"""Process this customer order and return the result as a valid JSON object only (no other text).

Customer ID: {customer_id}
Items:{items_text}

Calculate the total price in cents by multiplying quantity by unit_price for each item and summing them.

Return ONLY a JSON object with this exact structure:
{{
    "customer_id": "{customer_id}",
    "items": [
        {{"product_id": "...", "quantity": ..., "unit_price": ..., "line_total": ...}},
        ...
    ],
    "total": ...
}}

Where line_total for each item is quantity * unit_price, and total is the sum of all line_totals."""

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
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1500},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 2500},
        {"product_id": "PROD003", "quantity": 3, "unit_price": 800},
    ]

    result = build_order("CUST123", test_items)
    print("Order Details:")
    print(f"Customer ID: {result['customer_id']}")
    print("\nLine Items:")
    for item in result["items"]:
        print(
            f"  Product {item['product_id']}: {item['quantity']} x {item['unit_price']} cents = {item['line_total']} cents"
        )
    print(f"\nOrder Total: {result['total']} cents")

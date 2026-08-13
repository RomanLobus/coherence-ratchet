import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary for a customer.
    
    Args:
        customer_id: The ID of the customer
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()

    items_description = "\n".join(
        [
            f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
            for item in items
        ]
    )

    prompt = f"""Calculate the total for an order with the following items:
{items_description}

Please calculate the total price in cents by multiplying quantity by unit_price for each item and summing them up.
Return ONLY a JSON object with the calculated total as a number (in cents), like: {{"total": 12345}}"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text

    import json

    import re

    json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if json_match:
        total_data = json.loads(json_match.group())
        total = total_data.get("total", 0)
    else:
        total = 0

    return {"customer_id": customer_id, "items": items, "total": total}


if __name__ == "__main__":
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1000},
        {"product_id": "PROD002", "quantity": 3, "unit_price": 500},
        {"product_id": "PROD003", "quantity": 1, "unit_price": 2500},
    ]

    order = build_order("CUST123", test_items)
    print("Order:", order)
    print("\nExpected total: 2*1000 + 3*500 + 1*2500 = 2000 + 1500 + 2500 = 6000 cents")

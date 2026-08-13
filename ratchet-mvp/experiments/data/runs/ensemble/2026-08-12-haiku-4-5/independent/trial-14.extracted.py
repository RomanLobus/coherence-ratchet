import anthropic
import json


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude to structure the data properly.

    Args:
        customer_id: The ID of the customer
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)

    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()

    items_json = json.dumps(items)

    prompt = f"""Given the following customer order data, create a properly structured order dictionary.

Customer ID: {customer_id}
Items (as JSON): {items_json}

Calculate the total price by multiplying quantity × unit_price for each item and summing them all.
Return a JSON object with exactly these fields:
- customer_id: the customer ID
- line_items: array of items with product_id, quantity, unit_price (in cents), and line_total (quantity × unit_price in cents)
- order_total: sum of all line_totals in cents

Return ONLY valid JSON, no other text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text
    order = json.loads(response_text)

    return order


if __name__ == "__main__":
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},
        {"product_id": "PROD003", "quantity": 3, "unit_price": 599},
    ]

    order = build_order("CUST123", test_items)
    print(json.dumps(order, indent=2))

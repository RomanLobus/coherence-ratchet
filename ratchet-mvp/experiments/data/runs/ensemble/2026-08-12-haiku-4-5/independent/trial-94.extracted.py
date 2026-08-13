import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude AI to validate and process the order.

    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)

    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()

    # Prepare the message for Claude to validate and process the order
    items_description = "\n".join(
        [
            f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
            for item in items
        ]
    )

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Process this order and return a JSON response with the following structure:
{{
    "customer_id": "<customer_id>",
    "items": [
        {{"product_id": "<id>", "quantity": <qty>, "unit_price": <price_cents>, "line_total": <total_cents>}}
    ],
    "total": <total_cents>
}}

Customer ID: {customer_id}
Items:
{items_description}

For each item, calculate the line_total as quantity * unit_price.
Calculate the order total as the sum of all line totals.
Return ONLY the JSON, no other text.""",
            }
        ],
    )

    # Extract the JSON response from Claude
    response_text = message.content[0].text

    # Parse the JSON response
    import json

    order = json.loads(response_text)

    return order


if __name__ == "__main__":
    # Example usage
    sample_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},  # $19.99 each
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},  # $49.99
    ]

    order = build_order("CUST123", sample_items)
    print("Built Order:")
    print(order)

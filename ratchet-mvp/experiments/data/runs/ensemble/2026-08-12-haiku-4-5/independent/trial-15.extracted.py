import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and process the order data.

    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)

    Returns:
        A dictionary representing the order with customer, line_items, and total
    """
    client = anthropic.Anthropic()

    # Prepare the items information for Claude
    items_info = "\n".join(
        [
            f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
            for item in items
        ]
    )

    prompt = f"""Process this customer order and return a JSON response with the exact structure shown below.

Customer ID: {customer_id}
Items:
{items_info}

Return a JSON object with this exact structure (no markdown, just raw JSON):
{{
    "customer": "{customer_id}",
    "line_items": [
        {{"product_id": "...", "quantity": ..., "unit_price": ..., "line_total": ...}}
    ],
    "order_total": ...
}}

For each item, calculate the line_total as quantity * unit_price (in cents).
The order_total is the sum of all line_totals (in cents).
Return ONLY the JSON object, nothing else."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    import json

    response_text = message.content[0].text
    order = json.loads(response_text)

    return order

import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary from customer ID and items list.
    
    Args:
        customer_id: The ID of the customer
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Build the items description for Claude
    items_description = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Calculate the total price for this order and return a JSON response.

Customer ID: {customer_id}

Items:
{items_description}

Return a JSON object with:
- "customer_id": the customer ID
- "line_items": array of the items with their totals (quantity * unit_price in cents)
- "order_total": sum of all line item totals in cents

Return ONLY the JSON object, no other text."""
            }
        ]
    )
    
    # Parse the response
    import json
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order

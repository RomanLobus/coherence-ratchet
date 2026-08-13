import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Prepare the items for Claude to process
    items_str = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Process this order and return a JSON response with the following structure:
{{
  "customer_id": "<customer_id>",
  "line_items": [
    {{"product_id": "<id>", "quantity": <qty>, "unit_price": <price_cents>, "total": <line_total_cents>}}
  ],
  "order_total": <total_cents>
}}

Customer ID: {customer_id}

Items:
{items_str}

Calculate the total for each line item (quantity × unit_price) and the order total (sum of all line items).
Return ONLY valid JSON, no other text."""
            }
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    
    # Extract JSON from response (handle potential markdown formatting)
    if "
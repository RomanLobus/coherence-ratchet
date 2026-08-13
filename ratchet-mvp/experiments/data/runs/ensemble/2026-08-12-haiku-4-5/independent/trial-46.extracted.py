import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary for a customer.
    
    Args:
        customer_id: The ID of the customer
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer', 'line_items', and 'order_total'
    """
    client = anthropic.Anthropic()
    
    # Format items for the prompt
    items_text = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Process this order and return a JSON object with the following structure:
{{
  "customer": "<customer_id>",
  "line_items": [
    {{"product_id": "<id>", "quantity": <qty>, "unit_price": <cents>, "total": <cents>}},
    ...
  ],
  "order_total": <total_in_cents>
}}

Customer ID: {customer_id}

Items:
{items_text}

Calculate the total for each line item (quantity * unit_price) and the order total (sum of all line items).
Return ONLY the JSON object, no other text."""
            }
        ]
    )
    
    import json
    
    # Extract the JSON from the response
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order

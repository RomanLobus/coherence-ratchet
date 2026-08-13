import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Prepare the items description for Claude
    items_description = "Items to order:\n"
    for item in items:
        items_description += f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents\n"
    
    # Use Claude to validate and structure the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are an order processing system. Please validate and structure the following order data.

Customer ID: {customer_id}

{items_description}

Return a JSON object with the following structure:
{{
  "customer_id": "<customer_id>",
  "line_items": [
    {{
      "product_id": "<product_id>",
      "quantity": <quantity>,
      "unit_price": <unit_price_in_cents>,
      "subtotal": <quantity * unit_price>
    }}
  ],
  "order_total": <sum_of_all_subtotals>
}}

Return ONLY the JSON object, no other text."""
            }
        ]
    )
    
    # Parse the response from Claude
    response_text = message.content[0].text
    
    # Clean up the response text (remove markdown code blocks if present)
    if response_text.startswith("
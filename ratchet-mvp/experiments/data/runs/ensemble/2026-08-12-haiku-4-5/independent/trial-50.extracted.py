import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary for a customer.
    
    Args:
        customer_id: The customer ID
        items: A list of dictionaries each with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary representing the order with customer, line_items, and order_total
    """
    client = anthropic.Anthropic()
    
    # Prepare the order data for Claude
    order_data = {
        "customer_id": customer_id,
        "items": items
    }
    
    # Use Claude to process and validate the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Process this order data and return a valid JSON response with the following structure:
{{
    "customer_id": <customer_id>,
    "line_items": [
        {{
            "product_id": <product_id>,
            "quantity": <quantity>,
            "unit_price": <unit_price_in_cents>,
            "total": <quantity * unit_price>
        }}
    ],
    "order_total": <sum_of_all_line_item_totals>
}}

Order data: {order_data}

Return ONLY the JSON object, no additional text."""
            }
        ]
    )
    
    # Parse the response
    import json
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order

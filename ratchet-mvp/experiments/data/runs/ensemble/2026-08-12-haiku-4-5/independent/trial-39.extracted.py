import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Prepare the prompt for Claude
    items_description = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    prompt = f"""Given the following order items, calculate the total price in cents and return a valid JSON response.

Customer ID: {customer_id}

Items:
{items_description}

Please respond with ONLY a valid JSON object in this format:
{{
    "customer_id": "{customer_id}",
    "line_items": [
        {{"product_id": "...", "quantity": ..., "unit_price": ..., "total": ...}},
        ...
    ],
    "total": ...
}}

Where:
- Each line item's "total" is quantity * unit_price
- The order "total" is the sum of all line item totals
- All prices are in cents"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    
    # Extract JSON from the response
    import json
    
    # Try to parse the response as JSON
    try:
        order = json.loads(response_text)
    except json.JSONDecodeError:
        # If the response contains JSON wrapped in markdown code blocks, extract it
        import re
        json_match = re.search(r'
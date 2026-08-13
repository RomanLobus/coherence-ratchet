import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude AI.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary representing the order with customer_id, line_items, and order_total
    """
    client = anthropic.Anthropic()
    
    # Calculate totals for each item
    line_items = []
    total_cents = 0
    
    for item in items:
        item_total = item["quantity"] * item["unit_price"]
        total_cents += item_total
        line_items.append({
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "total": item_total
        })
    
    # Use Claude to format and validate the order
    prompt = f"""You are an order processing system. Format the following order data into a valid JSON response.

Customer ID: {customer_id}
Items: {line_items}
Total (in cents): {total_cents}

Return ONLY a valid JSON object with this structure:
{{
    "customer_id": "{customer_id}",
    "line_items": [list of items with product_id, quantity, unit_price, and total],
    "order_total": {total_cents}
}}"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    
    # Extract JSON from response
    import json
    import re
    
    # Find JSON in response
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group()
        order = json.loads(json_str)
    else:
        # Fallback to manual construction if Claude response isn't valid JSON
        order = {
            "customer_id": customer_id,
            "line_items": line_items,
            "order_total": total_cents
        }
    
    return order

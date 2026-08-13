import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary for a customer using Claude AI.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with customer, line_items, and order_total
    """
    client = anthropic.Anthropic()
    
    prompt = f"""Given the following order data, build a complete order dictionary. 
Customer ID: {customer_id}
Items: {items}

Return a JSON object with exactly these fields:
- "customer_id": the customer id
- "line_items": array of items with product_id, quantity, unit_price_cents, and line_total_cents
- "order_total_cents": total cost in cents (sum of all line totals)

Return ONLY valid JSON, no other text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    import json
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},
    ]
    
    order = build_order("CUST123", items)
    print("Order:", order)

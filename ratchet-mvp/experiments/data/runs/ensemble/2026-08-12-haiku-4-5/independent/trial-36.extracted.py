import anthropic


def build_order(customer_id: str, items: list) -> dict:
    """
    Build an order dictionary from customer ID and items list.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Format items for the prompt
    items_text = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    prompt = f"""Calculate the total for the following order:

Customer ID: {customer_id}

Items:
{items_text}

Calculate the total by multiplying quantity × unit_price for each item and summing them up.
Respond with ONLY a JSON object in this exact format (no markdown, no extra text):
{{"customer_id": "{customer_id}", "items": {items}, "total": <total_in_cents>}}"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract and parse the response
    response_text = message.content[0].text
    import json
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    # Example usage
    items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1000},  # $10.00
        {"product_id": "PROD002", "quantity": 1, "unit_price": 2500},  # $25.00
        {"product_id": "PROD003", "quantity": 3, "unit_price": 500},   # $5.00
    ]
    
    order = build_order("CUST123", items)
    print("Order:", order)
    
    # Verify the total
    expected_total = (2 * 1000) + (1 * 2500) + (3 * 500)
    print(f"Expected total: {expected_total} cents")
    print(f"Order total: {order['total']} cents")
    print(f"Match: {expected_total == order['total']}")

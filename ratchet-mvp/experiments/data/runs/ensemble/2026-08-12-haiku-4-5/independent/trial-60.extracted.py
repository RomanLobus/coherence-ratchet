import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary from customer_id and items.
    
    Args:
        customer_id: The customer's ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    items_str = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    prompt = f"""Given the following order details, calculate the total price and format as a JSON response.

Customer ID: {customer_id}
Items:
{items_str}

Please respond with a JSON object containing:
- "customer_id": the customer ID
- "items": the list of items with product_id, quantity, unit_price, and line_total (quantity * unit_price)
- "total": the sum of all line totals in cents

Respond ONLY with valid JSON, no additional text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    
    import json
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},
        {"product_id": "PROD003", "quantity": 3, "unit_price": 599},
    ]
    
    order = build_order("CUST123", items)
    print("Order:", order)

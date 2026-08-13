import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude API to validate and structure the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary containing customer, line_items, and order_total (in cents)
    """
    client = anthropic.Anthropic()
    
    items_text = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    prompt = f"""Given the following order details, create a structured order:

Customer ID: {customer_id}
Items:
{items_text}

Please calculate the total price in cents and return the order as a Python dictionary with:
1. 'customer_id': the customer ID
2. 'line_items': list of items with product_id, quantity, unit_price, and line_total (quantity * unit_price)
3. 'order_total': sum of all line totals in cents

Return ONLY the Python dictionary, no other text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    order_dict = eval(response_text)
    
    return order_dict

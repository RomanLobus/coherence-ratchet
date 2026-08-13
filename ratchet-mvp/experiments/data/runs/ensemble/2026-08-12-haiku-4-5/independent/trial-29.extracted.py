import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary from customer_id and items.
    
    Args:
        customer_id: The ID of the customer
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary representing the order with customer_id, line_items, and total (in cents)
    """
    client = anthropic.Anthropic()
    
    # Build the items description for Claude to process
    items_description = "Items to include in order:\n"
    for item in items:
        items_description += f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents\n"
    
    # Use Claude to calculate the total and validate the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Process this customer order and return the result as a Python dictionary string that I can evaluate.

Customer ID: {customer_id}

{items_description}

For each item, calculate the line total (quantity × unit_price). Then calculate the order total.

Return ONLY a valid Python dictionary with this exact structure (no markdown, no explanation):
{{"customer_id": "{customer_id}", "line_items": [{{"product_id": "...", "quantity": ..., "unit_price": ..., "line_total": ...}}], "total": ...}}

All prices are in cents."""
            }
        ]
    )
    
    # Extract the response text
    response_text = message.content[0].text.strip()
    
    # Parse the response as a Python dictionary
    order = eval(response_text)
    
    return order

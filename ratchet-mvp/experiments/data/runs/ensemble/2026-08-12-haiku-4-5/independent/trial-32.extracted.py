import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude AI.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary representing the order with customer, line items, and total
    """
    client = anthropic.Anthropic()
    
    # Calculate totals for each item
    line_items = []
    order_total_cents = 0
    
    for item in items:
        item_total = item['quantity'] * item['unit_price']
        order_total_cents += item_total
        line_items.append({
            'product_id': item['product_id'],
            'quantity': item['quantity'],
            'unit_price': item['unit_price'],
            'total': item_total
        })
    
    # Use Claude to format the order nicely
    prompt = f"""Given the following order information, create a well-structured order dictionary.
Customer ID: {customer_id}
Line Items: {line_items}
Order Total (in cents): {order_total_cents}

Return ONLY valid Python dictionary syntax with the following structure:
- customer_id: the customer ID
- line_items: list of line items with product_id, quantity, unit_price, and total
- order_total: the total in cents

Make sure all numeric values are integers and prices are in cents."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response to get the dictionary
    response_text = message.content[0].text
    
    # Extract the dictionary from the response
    # Find the start and end of the dictionary
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}') + 1
    
    if start_idx != -1 and end_idx > start_idx:
        dict_str = response_text[start_idx:end_idx]
        # Safely evaluate the dictionary string
        order = eval(dict_str)
        return order
    else:
        # Fallback if Claude's response format is unexpected
        return {
            'customer_id': customer_id,
            'line_items': line_items,
            'order_total': order_total_cents
        }


if __name__ == "__main__":
    # Example usage
    items = [
        {'product_id': 'PROD001', 'quantity': 2, 'unit_price': 1999},
        {'product_id': 'PROD002', 'quantity': 1, 'unit_price': 5999}
    ]
    
    order = build_order('CUST123', items)
    print("Order:", order)

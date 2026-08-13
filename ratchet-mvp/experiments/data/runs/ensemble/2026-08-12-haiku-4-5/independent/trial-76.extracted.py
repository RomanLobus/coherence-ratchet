import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary for a customer using Claude AI.
    
    Args:
        customer_id: The ID of the customer
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Prepare the prompt for Claude
    items_description = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: ${item['unit_price']/100:.2f}"
        for item in items
    ])
    
    prompt = f"""You are a helpful order processing assistant. Given the following customer order details, 
create a structured order dictionary.

Customer ID: {customer_id}
Items:
{items_description}

Please return ONLY a valid JSON object with the following structure:
{{
    "customer_id": "{customer_id}",
    "line_items": [
        {{
            "product_id": "...",
            "quantity": ...,
            "unit_price": ...,
            "total": ...
        }}
    ],
    "order_total": ...
}}

Where:
- line_items contains each item with product_id, quantity, unit_price (in cents), and total (quantity * unit_price in cents)
- order_total is the sum of all line item totals in cents

Return ONLY the JSON object, no other text."""
    
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
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    # Example usage
    items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1500},  # $15.00
        {"product_id": "PROD002", "quantity": 1, "unit_price": 2999},  # $29.99
        {"product_id": "PROD003", "quantity": 3, "unit_price": 500},   # $5.00
    ]
    
    order = build_order("CUST123", items)
    print("Order created:")
    import json
    print(json.dumps(order, indent=2))

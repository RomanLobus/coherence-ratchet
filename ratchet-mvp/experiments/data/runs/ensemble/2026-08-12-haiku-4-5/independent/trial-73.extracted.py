import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude API.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with product_id, quantity, and unit_price (in cents)
    
    Returns:
        Dictionary with customer_id, items, and total (in cents)
    """
    client = anthropic.Anthropic()
    
    # Create a prompt for Claude to validate and structure the order
    prompt = f"""Given the following customer order information, validate it and return a properly formatted order dictionary in JSON format.

Customer ID: {customer_id}
Items:
{chr(10).join(f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents" for item in items)}

Please return a JSON object with exactly these fields:
- customer_id: the customer ID
- items: array of items, each with product_id, quantity, and unit_price (in cents)
- total: the total order amount in cents (calculated as sum of quantity * unit_price for each item)

Return ONLY the JSON object, no additional text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    import json
    # Extract the JSON from Claude's response
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    # Example usage
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1500},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 3000},
        {"product_id": "PROD003", "quantity": 3, "unit_price": 500}
    ]
    
    order = build_order("CUST123", test_items)
    print("Order created:")
    print(f"Customer ID: {order['customer_id']}")
    print(f"Items: {order['items']}")
    print(f"Total: {order['total']} cents (${order['total']/100:.2f})")

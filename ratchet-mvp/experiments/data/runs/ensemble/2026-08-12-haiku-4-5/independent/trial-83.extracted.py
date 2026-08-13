import anthropic


def build_order(customer_id, items):
    """Build an order dictionary using Claude to validate and process the order.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Format items for the prompt
    items_str = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Process this order and return ONLY a valid JSON object with no additional text:
Customer ID: {customer_id}
Items:
{items_str}

Return a JSON object with:
- "customer_id": the customer ID
- "items": array of items (each with product_id, quantity, unit_price in cents, and line_total in cents)
- "total": total order amount in cents

Calculate line totals as quantity * unit_price and sum them for the total."""
            }
        ]
    )
    
    # Parse the response
    import json
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    # Example usage
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},  # $19.99
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},  # $49.99
    ]
    
    order = build_order("CUST123", test_items)
    print("Order created:")
    print(f"Customer ID: {order['customer_id']}")
    print(f"Items: {order['items']}")
    print(f"Total: ${order['total']/100:.2f}")

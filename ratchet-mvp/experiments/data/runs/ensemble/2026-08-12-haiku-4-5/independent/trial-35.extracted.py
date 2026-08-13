import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and structure the order.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary representing the order with customer, line items, and total
    """
    client = anthropic.Anthropic()
    
    # Prepare the items for Claude to validate
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
                "content": f"""Given the following order information, please validate it and return a JSON object with the order details.

Customer ID: {customer_id}
Items:
{items_str}

Please return a valid JSON object with the following structure:
{{
    "customer_id": "<customer_id>",
    "line_items": [
        {{
            "product_id": "<product_id>",
            "quantity": <quantity>,
            "unit_price": <unit_price_in_cents>,
            "item_total": <quantity * unit_price>
        }}
    ],
    "order_total": <sum of all item totals in cents>
}}

Return ONLY the JSON object, no other text."""
            }
        ]
    )
    
    # Extract the JSON from Claude's response
    response_text = message.content[0].text
    
    # Parse the JSON response
    import json
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    # Example usage
    sample_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},
        {"product_id": "PROD003", "quantity": 3, "unit_price": 999},
    ]
    
    order = build_order("CUST123", sample_items)
    print("Order built successfully:")
    print(f"Customer ID: {order['customer_id']}")
    print(f"Line Items: {order['line_items']}")
    print(f"Order Total: {order['order_total']} cents (${order['order_total']/100:.2f})")

import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and process the order.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    items_str = "\n".join(
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    )
    
    prompt = f"""Given the following order items for customer {customer_id}, calculate the total price and return a JSON response with the exact structure requested.

Items:
{items_str}

Please respond with ONLY a valid JSON object (no additional text) in this exact format:
{{
    "customer_id": "{customer_id}",
    "line_items": [
        {{"product_id": "product_id_value", "quantity": quantity_value, "unit_price": price_in_cents, "line_total": line_total_in_cents}},
        ...
    ],
    "order_total": total_in_cents
}}

Where:
- line_total for each item = quantity * unit_price
- order_total = sum of all line_totals
- All prices are in cents"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text.strip()
    
    import json
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    sample_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1500},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 2999},
        {"product_id": "PROD003", "quantity": 3, "unit_price": 500}
    ]
    
    order = build_order("CUST123", sample_items)
    print("Order created:")
    print(f"Customer ID: {order['customer_id']}")
    print(f"Line Items:")
    for item in order['line_items']:
        print(f"  - Product {item['product_id']}: {item['quantity']} x {item['unit_price']} cents = {item['line_total']} cents")
    print(f"Order Total: {order['order_total']} cents (${order['order_total']/100:.2f})")

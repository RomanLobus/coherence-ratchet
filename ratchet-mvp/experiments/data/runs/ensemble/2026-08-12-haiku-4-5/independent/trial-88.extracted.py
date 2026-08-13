import anthropic


def build_order(customer_id, items):
    """Build an order dictionary with customer info, line items, and total."""
    client = anthropic.Anthropic()
    
    # Prepare the items summary for Claude
    items_description = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are an order processing system. Given the following order details, calculate the total and return a JSON response.

Customer ID: {customer_id}
Items:
{items_description}

For each item, calculate: quantity × unit_price (in cents)
Calculate the total order amount by summing all line item totals.

Return ONLY a valid JSON object (no markdown, no code blocks) with this structure:
{{
    "customer": "{customer_id}",
    "line_items": [
        {{"product_id": "...", "quantity": ..., "unit_price": ..., "total": ...}},
        ...
    ],
    "order_total": ...
}}

All monetary values should be in cents as integers."""
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
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},  # $19.99 each
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},  # $49.99
        {"product_id": "PROD003", "quantity": 3, "unit_price": 500},   # $5.00 each
    ]
    
    order = build_order("CUST12345", test_items)
    print("Order Details:")
    print(f"Customer: {order['customer']}")
    print(f"Line Items:")
    for item in order['line_items']:
        print(f"  - Product {item['product_id']}: {item['quantity']} × {item['unit_price']} cents = {item['total']} cents")
    print(f"Order Total: {order['order_total']} cents (${order['order_total']/100:.2f})")

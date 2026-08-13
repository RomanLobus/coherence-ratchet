import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer ID
        items: A list of dictionaries with keys: product_id, quantity, unit_price (in cents)
    
    Returns:
        A dictionary containing customer, line_items, and order_total (in cents)
    """
    client = anthropic.Anthropic()
    
    # Prepare items summary for Claude
    items_summary = []
    total_cents = 0
    
    for item in items:
        subtotal = item['quantity'] * item['unit_price']
        total_cents += subtotal
        items_summary.append(
            f"- Product {item['product_id']}: {item['quantity']} unit(s) @ {item['unit_price']} cents each = {subtotal} cents"
        )
    
    # Use Claude to validate and format the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are an order processing assistant. Given the following order details, 
validate them and respond with ONLY a valid JSON object (no markdown, no explanation) with this structure:
{{"customer_id": string, "line_items": [list of items with product_id, quantity, unit_price, subtotal], "order_total": number}}

Customer ID: {customer_id}
Items:
{chr(10).join(items_summary)}
Total: {total_cents} cents"""
            }
        ]
    )
    
    # Parse the response
    import json
    response_text = message.content[0].text.strip()
    order = json.loads(response_text)
    
    # Ensure order has the correct structure
    if 'order_total' not in order:
        order['order_total'] = total_cents
    
    return order


if __name__ == "__main__":
    # Example usage
    sample_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1000},  # $10.00 each
        {"product_id": "PROD002", "quantity": 1, "unit_price": 2500},  # $25.00
    ]
    
    order = build_order("CUST123", sample_items)
    print("Generated Order:")
    import json
    print(json.dumps(order, indent=2))

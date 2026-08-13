import anthropic
import json


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and process the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Calculate the order total locally
    order_total = sum(item['quantity'] * item['unit_price'] for item in items)
    
    # Use Claude to validate and process the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Process this order and return a JSON object with the following structure:
{{
    "customer_id": "<customer_id>",
    "line_items": [
        {{"product_id": "<id>", "quantity": <qty>, "unit_price": <price_in_cents>, "line_total": <total_in_cents>}},
        ...
    ],
    "order_total": <total_in_cents>
}}

Customer ID: {customer_id}
Items: {json.dumps(items)}

Validate that:
1. All quantities are positive integers
2. All prices are positive integers (in cents)
3. Calculate line totals and order total correctly
4. Return ONLY valid JSON, no other text"""
            }
        ]
    )
    
    # Parse Claude's response
    response_text = message.content[0].text
    
    # Extract JSON from the response
    try:
        order = json.loads(response_text)
    except json.JSONDecodeError:
        # If Claude's response isn't pure JSON, try to extract it
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            order = json.loads(json_match.group())
        else:
            # Fallback to building the order directly
            line_items = []
            for item in items:
                line_items.append({
                    "product_id": item['product_id'],
                    "quantity": item['quantity'],
                    "unit_price": item['unit_price'],
                    "line_total": item['quantity'] * item['unit_price']
                })
            order = {
                "customer_id": customer_id,
                "line_items": line_items,
                "order_total": order_total
            }
    
    return order


if __name__ == "__main__":
    # Example usage
    test_items = [
        {"product_id": "SKU001", "quantity": 2, "unit_price": 1999},  # $19.99 each
        {"product_id": "SKU002", "quantity": 1, "unit_price": 4999},  # $49.99
    ]
    
    order = build_order("CUST123", test_items)
    print(json.dumps(order, indent=2))

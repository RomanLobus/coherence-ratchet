import anthropic
import json

def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude AI to process and validate the order data.
    
    Args:
        customer_id: The customer identifier
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    items_summary = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: ${item['unit_price']/100:.2f}"
        for item in items
    ])
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Process this customer order and return a JSON object with the following structure:
{{
  "customer_id": "<customer_id>",
  "line_items": [
    {{"product_id": "<id>", "quantity": <qty>, "unit_price": <price_in_cents>, "total": <line_total_in_cents>}}
  ],
  "order_total": <total_in_cents>
}}

Customer ID: {customer_id}
Items:
{items_summary}

Return ONLY the JSON object, no other text."""
            }
        ]
    )
    
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order

import anthropic
import json


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude API.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total_cents'
    """
    client = anthropic.Anthropic()
    
    prompt = f"""You are an order processing system. Given a customer ID and a list of items, 
create an order. Each item has a product_id, quantity, and unit_price_cents.

Calculate the line item totals and the order total in cents.

Return the response as a JSON object with this structure:
{{
    "customer_id": "<customer_id>",
    "line_items": [
        {{
            "product_id": "<product_id>",
            "quantity": <quantity>,
            "unit_price_cents": <unit_price_cents>,
            "total_cents": <quantity * unit_price_cents>
        }}
    ],
    "order_total_cents": <sum of all line item totals>
}}

Customer ID: {customer_id}
Items: {json.dumps(items)}

Return ONLY the JSON object, no other text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order

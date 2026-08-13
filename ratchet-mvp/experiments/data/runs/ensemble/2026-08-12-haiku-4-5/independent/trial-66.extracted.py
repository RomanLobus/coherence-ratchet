import anthropic
from typing import Any


def build_order(customer_id: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Build an order dictionary using Claude to process the order details.
    
    Args:
        customer_id: The ID of the customer
        items: A list of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    
    client = anthropic.Anthropic()
    
    items_description = "\n".join(
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    )
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Process this order and return a JSON response with the following structure:
{{
    "customer_id": "<customer_id>",
    "line_items": [
        {{"product_id": "<product_id>", "quantity": <quantity>, "unit_price": <unit_price_in_cents>, "line_total": <line_total_in_cents>}},
        ...
    ],
    "order_total": <total_in_cents>
}}

Customer ID: {customer_id}

Items:
{items_description}

Calculate the line total for each item (quantity * unit_price) and the order total (sum of all line totals).
Return ONLY the JSON, no other text."""
            }
        ]
    )
    
    response_text = message.content[0].text
    
    import json
    order = json.loads(response_text)
    
    return order

"""Module for building customer orders."""

import anthropic


def build_order(customer_id: str, items: list) -> dict:
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: A list of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary representing the order with customer, line items, and total
    """
    client = anthropic.Anthropic()
    
    # Prepare the items information for the API
    items_description = "\n".join(
        [f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: ${item['unit_price']/100:.2f}" 
         for item in items]
    )
    
    # Use Claude to calculate the order total and format the response
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Given the following order information, calculate the total and return a JSON object with the structure:
{{
    "customer_id": "<customer_id>",
    "line_items": [
        {{"product_id": "<id>", "quantity": <qty>, "unit_price_cents": <price>, "total_cents": <total>}},
        ...
    ],
    "order_total_cents": <total>
}}

Customer ID: {customer_id}
Items:
{items_description}

Return ONLY the JSON object, no other text."""
            }
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    
    # Extract JSON from response (it might be wrapped in markdown code blocks)
    if "
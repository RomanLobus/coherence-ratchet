import anthropic
import json


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude AI to validate and structure the order.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary with 'customer_id', 'items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Create a prompt for Claude to validate and build the order
    prompt = f"""Given the following order information, validate it and return a properly formatted order as JSON.

Customer ID: {customer_id}
Items: {json.dumps(items)}

Please validate that:
1. Customer ID is provided
2. Each item has product_id, quantity, and unit_price
3. Quantities and prices are positive numbers

Return a JSON object with this exact structure:
{{
  "customer_id": "<customer_id>",
  "items": [
    {{
      "product_id": "<product_id>",
      "quantity": <quantity>,
      "unit_price": <unit_price_in_cents>,
      "line_total": <quantity * unit_price>
    }}
  ],
  "order_total": <sum_of_all_line_totals>
}}

Only return the JSON object, no other text."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order

import anthropic
import json


def build_order(customer_id: str, items: list) -> dict:
    """
    Builds an order using Claude as an AI backbone for processing and validation.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Prepare the order data for Claude to process
    order_data = {
        "customer_id": customer_id,
        "items": items
    }
    
    # Use Claude to validate and process the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Process this customer order and return a JSON response.
                
Order data:
{json.dumps(order_data, indent=2)}

Please validate the order and return a JSON object with:
- customer_id: the customer ID
- items: array of line items with product_id, quantity, unit_price (in cents), and line_total (quantity * unit_price in cents)
- total: sum of all line totals in cents

Return ONLY valid JSON, no other text."""
            }
        ]
    )
    
    # Extract and parse the response
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    return order

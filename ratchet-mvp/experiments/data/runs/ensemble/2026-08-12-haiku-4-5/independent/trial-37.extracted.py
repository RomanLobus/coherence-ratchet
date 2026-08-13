import anthropic
import json


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude AI.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Prepare the items information for Claude
    items_description = json.dumps(items, indent=2)
    
    # Use Claude to help build and validate the order
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are an order processing system. Given a customer ID and a list of items with product IDs, quantities, and unit prices (in cents), create an order structure.

Customer ID: {customer_id}

Items:
{items_description}

Return a JSON object with the following structure:
- "customer": the customer ID
- "line_items": array of items with their calculated totals (quantity * unit_price, in cents)
- "order_total": sum of all line item totals (in cents)

Return only the JSON object, no additional text."""
            }
        ]
    )
    
    # Parse Claude's response
    response_text = message.content[0].text
    
    # Extract JSON from the response
    try:
        # Try to parse directly first
        order = json.loads(response_text)
    except json.JSONDecodeError:
        # If that fails, try to find JSON in the response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            order = json.loads(json_match.group())
        else:
            raise ValueError(f"Could not parse order from Claude's response: {response_text}")
    
    # Ensure the order has all required fields
    if "customer" not in order:
        order["customer"] = customer_id
    if "line_items" not in order:
        order["line_items"] = []
    if "order_total" not in order:
        order["order_total"] = 0
    
    return order

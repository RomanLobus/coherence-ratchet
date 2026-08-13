import anthropic
import json


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude API.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    
    client = anthropic.Anthropic()
    
    # Prepare the items description for Claude
    items_description = json.dumps(items, indent=2)
    
    # Use Claude to build the order with structured output
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Build an order for customer {customer_id} with the following items.
                
Items:
{items_description}

Return a JSON object with:
- customer_id: the customer ID
- line_items: array of items with product_id, quantity, unit_price (in cents), and line_total (quantity * unit_price, in cents)
- order_total: sum of all line_totals in cents

Return ONLY the JSON object, no other text."""
            }
        ]
    )
    
    # Extract the JSON from Claude's response
    response_text = message.content[0].text
    
    # Parse the JSON response
    order = json.loads(response_text)
    
    return order


if __name__ == "__main__":
    # Test the function
    sample_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},  # $19.99
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},  # $49.99
        {"product_id": "PROD003", "quantity": 3, "unit_price": 999},   # $9.99
    ]
    
    order = build_order("CUST123", sample_items)
    print(json.dumps(order, indent=2))

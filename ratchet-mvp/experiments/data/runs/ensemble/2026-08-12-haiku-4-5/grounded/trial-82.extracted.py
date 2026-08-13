import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to validate and transform the input data.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with product_id, quantity, and unit_price_cents
    
    Returns:
        A dictionary representing the order with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Prepare the prompt for Claude
    prompt = f"""You are an order processing system. Transform the following customer order data into a valid Order contract.

Customer ID: {customer_id}
Items: {json.dumps(items)}

Rules:
1. Use ONLY these top-level keys: order_id, customer_id, lines, total_cents, currency, created_at
2. Each entry in 'lines' must have ONLY: product_id, quantity, unit_price_cents
3. Generate a unique order_id (UUID format)
4. Set created_at to current ISO 8601 timestamp
5. Calculate total_cents by summing (quantity * unit_price_cents) for all items
6. Set currency to "USD"
7. Return ONLY valid JSON, no other text

Return the JSON order object directly."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract the response
    response_text = message.content[0].text
    
    # Parse the JSON response
    order = json.loads(response_text)
    
    return order

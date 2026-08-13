import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id: str, items: list) -> dict:
    """
    Build an order dictionary with canonical field set.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with product_id, quantity, unit_price_cents
        
    Returns:
        Order dictionary with canonical fields
    """
    client = anthropic.Anthropic()
    
    # Prepare the prompt for Claude to help build the order
    items_json = json.dumps(items)
    prompt = f"""You are an order processing system. Given the following items, calculate the total cost in cents and return a JSON response.

Customer ID: {customer_id}
Items: {items_json}

For each item, multiply quantity by unit_price_cents to get the line total.
Sum all line totals to get the order total in cents.

Return ONLY valid JSON with no markdown formatting, with this exact structure:
{{
  "lines": [
    {{"product_id": "...", "quantity": ..., "unit_price_cents": ...}},
    ...
  ],
  "total_cents": ...,
  "currency": "USD"
}}"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse Claude's response
    response_text = message.content[0].text
    order_data = json.loads(response_text)
    
    # Build the canonical order structure
    order = {
        "order_id": str(uuid4()),
        "customer_id": customer_id,
        "lines": order_data["lines"],
        "total_cents": order_data["total_cents"],
        "currency": order_data["currency"],
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return order

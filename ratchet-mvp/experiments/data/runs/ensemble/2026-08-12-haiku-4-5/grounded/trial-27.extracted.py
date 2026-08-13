import anthropic
import json
from datetime import datetime
import uuid


def build_order(customer_id: str, items: list) -> dict:
    """
    Build an order dictionary from customer_id and items list.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        Order dictionary with canonical field set
    """
    client = anthropic.Anthropic()
    
    items_description = json.dumps(items, indent=2)
    
    prompt = f"""You are an order processing system. Given the following items, calculate the order total and format the response as valid JSON.

Customer ID: {customer_id}

Items:
{items_description}

Calculate the total by summing (quantity * unit_price_cents) for each item.
Currency is always USD.

Return ONLY a valid JSON object with this exact structure:
{{
  "lines": [
    {{
      "product_id": "...",
      "quantity": ...,
      "unit_price_cents": ...
    }}
  ],
  "total_cents": ...
}}

Do not include any markdown formatting, code blocks, or explanation. Return only the JSON object."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text.strip()
    
    response_data = json.loads(response_text)
    
    order = {
        "order_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "lines": response_data["lines"],
        "total_cents": response_data["total_cents"],
        "currency": "USD",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return order

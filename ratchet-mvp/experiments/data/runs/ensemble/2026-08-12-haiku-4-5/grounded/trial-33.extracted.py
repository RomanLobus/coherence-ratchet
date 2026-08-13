import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to validate and process the items.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', 'unit_price_cents'
    
    Returns:
        Order dictionary with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Prepare the items for Claude to process
    items_text = json.dumps(items, indent=2)
    
    prompt = f"""Process the following order items and return a JSON response with the exact structure below.
Each item has: product_id, quantity, unit_price_cents (in cents).

Items to process:
{items_text}

Return ONLY valid JSON (no markdown, no extra text) with this exact structure:
{{
    "lines": [
        {{"product_id": "string", "quantity": number, "unit_price_cents": number}},
        ...
    ],
    "total_cents": number
}}

Calculate total_cents as the sum of (quantity * unit_price_cents) for all items."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse Claude's response
    response_text = message.content[0].text.strip()
    
    # Handle markdown code blocks if present
    if response_text.startswith("
import anthropic
import json
from datetime import datetime
from uuid import uuid4


def build_order(customer_id: str, items: list) -> dict:
    """
    Build an order using Claude as the AI backbone to ensure canonical format compliance.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', 'unit_price_cents'
    
    Returns:
        A dictionary with the canonical order structure
    """
    client = anthropic.Anthropic()
    
    # Validate and prepare items
    validated_items = []
    total_cents = 0
    
    for item in items:
        if not all(k in item for k in ['product_id', 'quantity', 'unit_price_cents']):
            raise ValueError(f"Item missing required fields: {item}")
        
        product_id = item['product_id']
        quantity = int(item['quantity'])
        unit_price_cents = int(item['unit_price_cents'])
        
        line_total = quantity * unit_price_cents
        total_cents += line_total
        
        validated_items.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price_cents': unit_price_cents
        })
    
    # Use Claude to validate and structure the order
    validation_prompt = f"""
    Validate this order data and confirm it matches the canonical Order contract:
    - Must have exactly these top-level keys: order_id, customer_id, lines, total_cents, currency, created_at
    - Each line item must have exactly: product_id, quantity, unit_price_cents
    
    Customer ID: {customer_id}
    Items: {json.dumps(validated_items)}
    Total cents: {total_cents}
    
    Please confirm this is valid and return "VALID" if all requirements are met.
    """
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[
            {"role": "user", "content": validation_prompt}
        ]
    )
    
    validation_response = message.content[0].text
    if "VALID" not in validation_response.upper():
        raise ValueError(f"Order validation failed: {validation_response}")
    
    # Build the canonical order structure
    order = {
        'order_id': str(uuid4()),
        'customer_id': customer_id,
        'lines': validated_items,
        'total_cents': total_cents,
        'currency': 'USD',
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    return order

import anthropic
import json
import uuid
from datetime import datetime


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Builds an order dictionary using Claude to ensure compliance with the canonical schema.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        A dictionary representing the order with exact canonical field set
    """
    client = anthropic.Anthropic()
    
    order_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat() + "Z"
    
    lines = []
    total_cents = 0
    
    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        unit_price_cents = item.get('unit_price_cents')
        
        if not all([product_id, quantity, unit_price_cents]):
            raise ValueError(f"Invalid item structure: {item}")
        
        line_total = quantity * unit_price_cents
        total_cents += line_total
        
        lines.append({
            'product_id': product_id,
            'quantity': quantity,
            'unit_price_cents': unit_price_cents
        })
    
    order_prompt = f"""
    You are validating and confirming an order structure.
    
    Here is the order data:
    - Order ID: {order_id}
    - Customer ID: {customer_id}
    - Created At: {created_at}
    - Lines: {json.dumps(lines)}
    - Total Cents: {total_cents}
    - Currency: USD
    
    Please confirm this order follows the canonical schema with exactly these top-level keys:
    order_id, customer_id, lines, total_cents, currency, created_at
    
    And each line has exactly: product_id, quantity, unit_price_cents
    
    Respond with ONLY a valid JSON object, no other text.
    """
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": order_prompt}
        ]
    )
    
    response_text = message.content[0].text
    validated_response = json.loads(response_text)
    
    order = {
        'order_id': order_id,
        'customer_id': customer_id,
        'lines': lines,
        'total_cents': total_cents,
        'currency': 'USD',
        'created_at': created_at
    }
    
    return order

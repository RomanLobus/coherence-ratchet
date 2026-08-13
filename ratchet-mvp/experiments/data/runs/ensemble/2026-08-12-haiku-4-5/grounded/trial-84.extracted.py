import anthropic
import json


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order using Claude to generate a unique order ID.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', 'unit_price_cents'
    
    Returns:
        A dictionary representing the order with canonical field set
    """
    client = anthropic.Anthropic()
    
    items_description = "\n".join([
        f"- Product {item['product_id']}: {item['quantity']} units at {item['unit_price_cents']} cents each"
        for item in items
    ])
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Generate a unique order ID for a new order. 
The order ID should be a string that looks like an order identifier (e.g., "ORD-2024-001234").
Respond with ONLY the order ID string, nothing else.

Customer ID: {customer_id}
Items being ordered:
{items_description}"""
            }
        ]
    )
    
    order_id = message.content[0].text.strip()
    
    lines = []
    total_cents = 0
    
    for item in items:
        product_id = item['product_id']
        quantity = item['quantity']
        unit_price_cents = item['unit_price_cents']
        
        line_total = quantity * unit_price_cents
        total_cents += line_total
        
        line = {
            'product_id': product_id,
            'quantity': quantity,
            'unit_price_cents': unit_price_cents
        }
        lines.append(line)
    
    from datetime import datetime
    created_at = datetime.utcnow().isoformat() + "Z"
    
    order = {
        'order_id': order_id,
        'customer_id': customer_id,
        'lines': lines,
        'total_cents': total_cents,
        'currency': 'USD',
        'created_at': created_at
    }
    
    return order


if __name__ == "__main__":
    test_items = [
        {'product_id': 'PROD-001', 'quantity': 2, 'unit_price_cents': 1999},
        {'product_id': 'PROD-002', 'quantity': 1, 'unit_price_cents': 4999},
    ]
    
    order = build_order('CUST-12345', test_items)
    print(json.dumps(order, indent=2))

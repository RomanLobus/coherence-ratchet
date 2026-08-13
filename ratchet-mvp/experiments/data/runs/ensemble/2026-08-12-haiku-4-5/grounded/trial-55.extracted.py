import anthropic
import json
import uuid
from datetime import datetime


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        A dictionary with order_id, customer_id, lines, total_cents, currency, created_at
    """
    client = anthropic.Anthropic()
    
    prompt = f"""Given this customer order data, return a valid JSON order object.

Customer ID: {customer_id}
Items to order:
{json.dumps(items, indent=2)}

Return ONLY a valid JSON object (no markdown, no code blocks) with these exact fields:
- order_id: A unique identifier (UUID format)
- customer_id: The provided customer ID
- lines: Array of line items, each with product_id, quantity, unit_price_cents
- total_cents: Sum of (quantity * unit_price_cents) for all lines
- currency: "USD"
- created_at: Current ISO 8601 timestamp

Ensure all monetary values are in cents (integers). Return only the JSON object, nothing else."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    order = json.loads(response_text)
    
    if not isinstance(order.get("lines"), list):
        order["lines"] = []
        for item in items:
            order["lines"].append({
                "product_id": item.get("product_id"),
                "quantity": item.get("quantity"),
                "unit_price_cents": item.get("unit_price_cents")
            })
    
    if "order_id" not in order or not order["order_id"]:
        order["order_id"] = str(uuid.uuid4())
    
    if "customer_id" not in order or not order["customer_id"]:
        order["customer_id"] = customer_id
    
    if "currency" not in order or not order["currency"]:
        order["currency"] = "USD"
    
    if "created_at" not in order or not order["created_at"]:
        order["created_at"] = datetime.utcnow().isoformat() + "Z"
    
    if "total_cents" not in order or order["total_cents"] is None:
        total = sum(line.get("quantity", 0) * line.get("unit_price_cents", 0) 
                   for line in order.get("lines", []))
        order["total_cents"] = total
    
    keys = {"order_id", "customer_id", "lines", "total_cents", "currency", "created_at"}
    order = {k: order[k] for k in keys if k in order}
    
    return order

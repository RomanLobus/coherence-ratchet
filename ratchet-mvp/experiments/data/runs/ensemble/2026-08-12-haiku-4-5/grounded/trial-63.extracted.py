import anthropic
import json
import uuid
from datetime import datetime


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude to validate and structure the data.
    
    Args:
        customer_id: The customer ID for the order
        items: List of dicts with keys: product_id, quantity, unit_price_cents
    
    Returns:
        Order dictionary with canonical field set
    """
    client = anthropic.Anthropic()
    
    # Create the order structure by asking Claude to validate and organize
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Given these items for an order, create a valid order JSON response.
                
Customer ID: {customer_id}
Items: {json.dumps(items)}

Return ONLY a valid JSON object with this exact structure (no markdown, no explanation):
{{
    "order_id": "unique-uuid-string",
    "customer_id": "the-customer-id",
    "lines": [
        {{
            "product_id": "product-id",
            "quantity": number,
            "unit_price_cents": number
        }}
    ],
    "total_cents": number,
    "currency": "USD",
    "created_at": "ISO-8601-datetime-string"
}}

Calculate total_cents as sum of (quantity * unit_price_cents) for all items."""
            }
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text.strip()
    order = json.loads(response_text)
    
    # Ensure all required fields are present and properly formatted
    if "order_id" not in order or not order["order_id"]:
        order["order_id"] = str(uuid.uuid4())
    
    if "created_at" not in order or not order["created_at"]:
        order["created_at"] = datetime.utcnow().isoformat() + "Z"
    
    if "currency" not in order:
        order["currency"] = "USD"
    
    if "total_cents" not in order:
        order["total_cents"] = sum(line["quantity"] * line["unit_price_cents"] for line in order.get("lines", []))
    
    # Ensure only canonical fields are present
    canonical_fields = {"order_id", "customer_id", "lines", "total_cents", "currency", "created_at"}
    filtered_order = {k: v for k, v in order.items() if k in canonical_fields}
    
    # Ensure lines have only canonical fields
    if "lines" in filtered_order:
        line_fields = {"product_id", "quantity", "unit_price_cents"}
        filtered_order["lines"] = [
            {k: v for k, v in line.items() if k in line_fields}
            for line in filtered_order["lines"]
        ]
    
    return filtered_order

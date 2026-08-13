import anthropic
import json
from datetime import datetime
import uuid


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary with canonical field set.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', and 'unit_price_cents'
    
    Returns:
        Order dictionary with canonical fields
    """
    
    client = anthropic.Anthropic()
    
    tools = [
        {
            "name": "create_order",
            "description": "Create an order with the canonical field structure",
            "input_schema": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Unique order identifier"
                    },
                    "customer_id": {
                        "type": "string",
                        "description": "Customer identifier"
                    },
                    "lines": {
                        "type": "array",
                        "description": "Order line items",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {
                                    "type": "string",
                                    "description": "Product identifier"
                                },
                                "quantity": {
                                    "type": "integer",
                                    "description": "Quantity ordered"
                                },
                                "unit_price_cents": {
                                    "type": "integer",
                                    "description": "Price per unit in cents"
                                }
                            },
                            "required": ["product_id", "quantity", "unit_price_cents"]
                        }
                    },
                    "total_cents": {
                        "type": "integer",
                        "description": "Total order amount in cents"
                    },
                    "currency": {
                        "type": "string",
                        "description": "Currency code"
                    },
                    "created_at": {
                        "type": "string",
                        "description": "ISO 8601 timestamp of order creation"
                    }
                },
                "required": ["order_id", "customer_id", "lines", "total_cents", "currency", "created_at"]
            }
        }
    ]
    
    items_str = json.dumps(items, indent=2)
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=tools,
        messages=[
            {
                "role": "user",
                "content": f"""Create an order for customer {customer_id} with the following items:

{items_str}

Use the create_order tool to build the order with:
- A unique order_id (use UUID format)
- The provided customer_id
- Line items with product_id, quantity, and unit_price_cents from the items
- Calculate total_cents as sum of (quantity * unit_price_cents) for each line
- Use 'USD' as currency
- Use current ISO 8601 timestamp for created_at"""
            }
        ]
    )
    
    for content_block in message.content:
        if content_block.type == "tool_use" and content_block.name == "create_order":
            order_data = content_block.input
            
            order = {
                "order_id": order_data.get("order_id", str(uuid.uuid4())),
                "customer_id": order_data.get("customer_id", customer_id),
                "lines": order_data.get("lines", []),
                "total_cents": order_data.get("total_cents", 0),
                "currency": order_data.get("currency", "USD"),
                "created_at": order_data.get("created_at", datetime.utcnow().isoformat() + "Z")
            }
            
            return order
    
    total_cents = sum(item.get("quantity", 0) * item.get("unit_price_cents", 0) for item in items)
    
    order = {
        "order_id": str(uuid.uuid4()),
        "customer_id": customer_id,
        "lines": [
            {
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "unit_price_cents": item["unit_price_cents"]
            }
            for item in items
        ],
        "total_cents": total_cents,
        "currency": "USD",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return order

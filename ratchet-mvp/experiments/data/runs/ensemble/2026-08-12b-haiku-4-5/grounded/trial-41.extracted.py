import json
from datetime import datetime
from anthropic import Anthropic

def build_order(customer_id, items):
    """
    Build an order dictionary from customer_id and items.
    
    Args:
        customer_id: The customer identifier
        items: List of dicts with 'product_id', 'quantity', 'unit_price_cents'
    
    Returns:
        Dict with keys: order_id, customer_id, lines, total_cents, currency, created_at
    """
    client = Anthropic()
    conversation_history = []
    
    # First turn: ask Claude to help build the order
    user_message = f"""I need to build an order. Here's the data:
- customer_id: {customer_id}
- items: {json.dumps(items)}

Please help me structure this into a proper order. I need:
1. An order_id (you can generate a reasonable format)
2. Line items with product_id, quantity, unit_price_cents
3. Total calculation
4. Currency (assume USD)
5. Timestamp

What should the structure look like?"""
    
    conversation_history.append({"role": "user", "content": user_message})
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=conversation_history
    )
    
    assistant_response = response.content[0].text
    conversation_history.append({"role": "assistant", "content": assistant_response})
    
    # Second turn: ask Claude to validate and provide the exact JSON structure
    user_message = f"""Now, based on your suggestion, please provide the exact JSON structure for this order. Make sure:
1. order_id is in format "ORD-" followed by a timestamp-based identifier
2. lines array has exactly the schema: product_id, quantity, unit_price_cents
3. total_cents is calculated correctly (sum of quantity * unit_price for each line)
4. currency is "USD"
5. created_at is ISO 8601 format

Just provide the complete JSON object, nothing else."""
    
    conversation_history.append({"role": "user", "content": user_message})
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=conversation_history
    )
    
    # Extract the JSON from Claude's response
    json_response = response.content[0].text
    
    # Try to find and parse JSON from the response
    # Look for JSON object pattern
    start_idx = json_response.find('{')
    end_idx = json_response.rfind('}') + 1
    
    if start_idx != -1 and end_idx > start_idx:
        json_str = json_response[start_idx:end_idx]
        order = json.loads(json_str)
    else:
        # Fallback: build the order manually if Claude didn't provide valid JSON
        import time
        order_id = f"ORD-{int(time.time())}"
        
        lines = []
        total_cents = 0
        
        for item in items:
            line = {
                "product_id": item["product_id"],
                "quantity": item["quantity"],
                "unit_price_cents": item["unit_price_cents"]
            }
            lines.append(line)
            total_cents += item["quantity"] * item["unit_price_cents"]
        
        order = {
            "order_id": order_id,
            "customer_id": customer_id,
            "lines": lines,
            "total_cents": total_cents,
            "currency": "USD",
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
    
    # Validate the order structure
    required_keys = {"order_id", "customer_id", "lines", "total_cents", "currency", "created_at"}
    if not all(key in order for key in required_keys):
        # Rebuild with correct structure
        import time
        order_id = order.get("order_id", f"ORD-{int(time.time())}")
        
        lines = order.get("lines", [])
        if not lines:
            lines = []
            for item in items:
                line = {
                    "product_id": item["product_id"],
                    "quantity": item["quantity"],
                    "unit_price_cents": item["unit_price_cents"]
                }
                lines.append(line)
        
        total_cents = order.get("total_cents", 0)
        if total_cents == 0:
            total_cents = sum(line.get("quantity", 0) * line.get("unit_price_cents", 0) for line in lines)
        
        order = {
            "order_id": order_id,
            "customer_id": customer_id,
            "lines": lines,
            "total_cents": total_cents,
            "currency": order.get("currency", "USD"),
            "created_at": order.get("created_at", datetime.utcnow().isoformat() + "Z")
        }
    
    return order

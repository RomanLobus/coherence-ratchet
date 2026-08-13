import anthropic
import json

def charge_customer(order, gateway):
    """
    Charge a customer for an order with automatic retry on transient failures.
    
    Args:
        order: Dictionary containing 'id' and 'amount' keys
        gateway: Gateway object with submit(order_id, amount_cents) method
    
    Returns:
        The result of the charge submission
    """
    client = anthropic.Anthropic()
    
    amount_cents = int(order['amount'] * 100)
    order_id = order['id']
    
    tools = [
        {
            "name": "submit_charge",
            "description": "Submit a charge to the payment gateway",
            "input_schema": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to charge"
                    },
                    "amount_cents": {
                        "type": "integer",
                        "description": "The amount to charge in cents"
                    }
                },
                "required": ["order_id", "amount_cents"]
            }
        }
    ]
    
    messages = [
        {
            "role": "user",
            "content": f"Please charge order {order_id} for {amount_cents} cents. If you get a transient error, retry the charge submission. Keep retrying until you get a successful result or a non-transient error."
        }
    ]
    
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )
        
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, 'text'):
                    return {"status": "completed", "message": block.text}
            return {"status": "completed", "message": "Charge processed"}
        
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if block.name == "submit_charge":
                        try:
                            result = gateway.submit(block.input["order_id"], block.input["amount_cents"])
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result)
                            })
                        except Exception as e:
                            error_msg = str(e)
                            if "transient" in error_msg.lower() or "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": json.dumps({"error": error_msg, "transient": True}),
                                    "is_error": True
                                })
                            else:
                                raise
            
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            break
    
    return {"status": "failed", "message": "Max retries exceeded"}

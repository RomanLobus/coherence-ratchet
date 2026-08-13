import anthropic
import json


def charge_customer(order: dict, gateway) -> dict:
    """
    Charge a customer using the provided gateway.
    
    Converts the order amount to cents, submits the charge, and retries on transient failure.
    Uses Claude with tool_use to handle the retry logic intelligently.
    
    Args:
        order: Dictionary with 'id' and 'amount' keys
        gateway: Object with submit(order_id, amount_cents) method
        
    Returns:
        Dictionary with charge result
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
                        "description": "The amount in cents to charge"
                    }
                },
                "required": ["order_id", "amount_cents"]
            }
        }
    ]
    
    messages = [
        {
            "role": "user",
            "content": f"Please charge customer for order {order_id} with amount {amount_cents} cents. Retry up to 3 times if you get a transient failure (network error, timeout, etc). Return the final result."
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
                    return {
                        "success": True,
                        "message": block.text,
                        "order_id": order_id,
                        "amount_cents": amount_cents
                    }
            return {
                "success": False,
                "message": "No response from Claude",
                "order_id": order_id
            }
        
        if response.stop_reason == "tool_use":
            tool_results = []
            
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    
                    if tool_name == "submit_charge":
                        try:
                            result = gateway.submit(
                                tool_input["order_id"],
                                tool_input["amount_cents"]
                            )
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result)
                            })
                        except Exception as e:
                            error_message = str(e)
                            if "transient" in error_message.lower() or "timeout" in error_message.lower() or "network" in error_message.lower():
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": json.dumps({"error": "transient_failure", "message": error_message}),
                                    "is_error": True
                                })
                            else:
                                return {
                                    "success": False,
                                    "error": error_message,
                                    "order_id": order_id
                                }
            
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
    
    return {
        "success": False,
        "message": "Max iterations reached",
        "order_id": order_id
    }

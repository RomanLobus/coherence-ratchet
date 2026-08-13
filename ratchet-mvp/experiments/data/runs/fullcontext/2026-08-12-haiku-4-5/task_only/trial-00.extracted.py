import anthropic
import json
import time
from typing import Any


def charge_customer(order: dict[str, Any], gateway: Any) -> dict[str, Any]:
    """
    Charge a customer using the provided order and payment gateway.
    
    This function converts the order amount to integer cents and submits
    the charge via the gateway, with automatic retry logic for transient failures.
    
    Args:
        order: Dictionary containing 'id' and 'amount' keys
        gateway: Payment gateway object with submit method
    
    Returns:
        Dictionary containing the charge result with status and details
    """
    client = anthropic.Anthropic()
    
    amount_cents = int(float(order['amount']) * 100)
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
                        "description": "The unique identifier for the order"
                    },
                    "amount_cents": {
                        "type": "integer",
                        "description": "The charge amount in cents"
                    }
                },
                "required": ["order_id", "amount_cents"]
            }
        },
        {
            "name": "retry_charge",
            "description": "Retry a failed charge after a brief delay",
            "input_schema": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to retry"
                    },
                    "amount_cents": {
                        "type": "integer",
                        "description": "The charge amount in cents"
                    },
                    "retry_count": {
                        "type": "integer",
                        "description": "Number of retries attempted"
                    }
                },
                "required": ["order_id", "amount_cents", "retry_count"]
            }
        }
    ]
    
    messages = [
        {
            "role": "user",
            "content": f"Please charge the customer for order {order_id} with amount {amount_cents} cents. Use the submit_charge tool. If you get a transient failure, retry up to 3 times using the retry_charge tool."
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
                        "status": "completed",
                        "result": block.text,
                        "order_id": order_id,
                        "amount_cents": amount_cents
                    }
            break
        
        if response.stop_reason == "tool_use":
            tool_calls = [block for block in response.content if block.type == "tool_use"]
            
            messages.append({"role": "assistant", "content": response.content})
            
            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call.name
                tool_input = tool_call.input
                
                if tool_name == "submit_charge":
                    try:
                        result = gateway.submit(tool_input["order_id"], tool_input["amount_cents"])
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": json.dumps({"success": True, "result": result})
                        })
                    except Exception as e:
                        error_msg = str(e)
                        is_transient = "transient" in error_msg.lower() or "timeout" in error_msg.lower()
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": json.dumps({
                                "success": False,
                                "error": error_msg,
                                "transient": is_transient
                            })
                        })
                
                elif tool_name == "retry_charge":
                    time.sleep(1)
                    try:
                        result = gateway.submit(tool_input["order_id"], tool_input["amount_cents"])
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": json.dumps({"success": True, "result": result, "retry_count": tool_input["retry_count"]})
                        })
                    except Exception as e:
                        error_msg = str(e)
                        is_transient = "transient" in error_msg.lower() or "timeout" in error_msg.lower()
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": json.dumps({
                                "success": False,
                                "error": error_msg,
                                "transient": is_transient,
                                "retry_count": tool_input["retry_count"]
                            })
                        })
            
            messages.append({"role": "user", "content": tool_results})
        else:
            break
    
    return {
        "status": "failed",
        "error": "Max iterations reached",
        "order_id": order_id,
        "amount_cents": amount_cents
    }

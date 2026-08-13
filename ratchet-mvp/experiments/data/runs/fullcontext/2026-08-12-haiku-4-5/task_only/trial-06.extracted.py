import anthropic
import json


def charge_customer(order: dict, gateway) -> dict:
    """
    Charge a customer using the provided gateway.
    
    Converts the order amount to integer cents and submits the charge,
    with automatic retry logic for transient failures using Claude.
    
    Args:
        order: Dictionary containing 'id' and 'amount' keys
        gateway: Payment gateway with submit(order_id, amount_cents) method
        
    Returns:
        Dictionary with charge result
    """
    
    # Convert amount to cents
    amount_cents = int(order['amount'] * 100)
    order_id = order['id']
    
    # Use Claude to handle the retry logic
    client = anthropic.Anthropic()
    
    # Define tools for the charge operation
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
        },
        {
            "name": "handle_transient_error",
            "description": "Handle a transient error and retry the charge",
            "input_schema": {
                "type": "object",
                "properties": {
                    "error_message": {
                        "type": "string",
                        "description": "The error message from the failed charge"
                    },
                    "retry_count": {
                        "type": "integer",
                        "description": "Number of retries attempted so far"
                    }
                },
                "required": ["error_message", "retry_count"]
            }
        }
    ]
    
    # Prepare the initial prompt for Claude
    prompt = f"""You are a billing assistant helping to process a customer charge.
    
Order ID: {order_id}
Amount in cents: {amount_cents}

Your task is to submit this charge to the payment gateway using the submit_charge tool. 
If you encounter a transient error (like connection timeout or temporary service unavailability), 
use the handle_transient_error tool to manage retries.

Please proceed with submitting the charge."""

    messages = [
        {"role": "user", "content": prompt}
    ]
    
    max_iterations = 10
    iteration = 0
    result = None
    
    while iteration < max_iterations:
        iteration += 1
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )
        
        # Check if we're done
        if response.stop_reason == "end_turn":
            # Extract the final response
            for block in response.content:
                if hasattr(block, 'text'):
                    result = {"status": "completed", "message": block.text}
            break
        
        # Process tool calls
        if response.stop_reason == "tool_use":
            tool_results = []
            
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    
                    if tool_name == "submit_charge":
                        try:
                            # Call the actual gateway
                            charge_result = gateway.submit(
                                tool_input["order_id"],
                                tool_input["amount_cents"]
                            )
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(charge_result)
                            })
                            result = charge_result
                        except Exception as e:
                            error_msg = str(e)
                            # Check if it's a transient error
                            if "transient" in error_msg.lower() or "timeout" in error_msg.lower() or "temporarily" in error_msg.lower():
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": json.dumps({
                                        "status": "error",
                                        "error_type": "transient",
                                        "message": error_msg
                                    })
                                })
                            else:
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": json.dumps({
                                        "status": "error",
                                        "error_type": "fatal",
                                        "message": error_msg
                                    })
                                })
                                # Don't retry on fatal errors
                                result = {
                                    "status": "failed",
                                    "error": error_msg
                                }
                                break
                    
                    elif tool_name == "handle_transient_error":
                        # Acknowledge the retry handling
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps({
                                "status": "retry_acknowledged",
                                "message": f"Handling transient error, retry attempt {tool_input.get('retry_count', 1)}"
                            })
                        })
            
            if result and result.get("status") == "failed":
                break
            
            # Add assistant response and tool results to messages
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            # Unexpected stop reason
            break
    
    # Return result with proper format
    if result is None:
        result = {
            "status": "failed",
            "error": "Failed to process charge after maximum retries"
        }
    
    return result

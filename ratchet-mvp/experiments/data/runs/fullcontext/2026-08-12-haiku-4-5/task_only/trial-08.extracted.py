import anthropic


def charge_customer(order: dict, gateway) -> dict:
    """
    Charge a customer by converting the order amount to cents and submitting via gateway.
    Uses Claude with tool_use to handle retries on transient failures.
    
    Args:
        order: Dictionary with 'id' and 'amount' keys
        gateway: Gateway object with submit(order_id, amount_cents) method
        
    Returns:
        Dictionary with charge result
    """
    client = anthropic.Anthropic()
    
    # Convert amount to cents
    amount_cents = int(order['amount'] * 100)
    order_id = order['id']
    
    # Define tools for the billing process
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
            "name": "handle_retry",
            "description": "Handle a transient failure and retry the charge",
            "input_schema": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "The reason for retry"
                    },
                    "retry_count": {
                        "type": "integer",
                        "description": "Current retry attempt number"
                    }
                },
                "required": ["reason", "retry_count"]
            }
        }
    ]
    
    # Initial message to Claude
    messages = [
        {
            "role": "user",
            "content": f"""Process a charge for order {order_id} with amount {amount_cents} cents.
            Submit the charge using the submit_charge tool. If you encounter a transient failure 
            (network error, timeout, etc.), use the handle_retry tool to retry. 
            Continue retrying up to 3 times on transient failures."""
        }
    ]
    
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Call Claude with tools
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )
        
        # Check if Claude wants to use a tool
        if response.stop_reason == "tool_use":
            # Find the tool use block
            tool_use_block = None
            for block in response.content:
                if block.type == "tool_use":
                    tool_use_block = block
                    break
            
            if not tool_use_block:
                break
                
            tool_name = tool_use_block.name
            tool_input = tool_use_block.input
            tool_use_id = tool_use_block.id
            
            # Process tool calls
            if tool_name == "submit_charge":
                try:
                    # Submit the charge via gateway
                    result = gateway.submit(tool_input["order_id"], tool_input["amount_cents"])
                    
                    # Add assistant message and tool result
                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": f"Charge submitted successfully: {result}"
                            }
                        ]
                    })
                    
                    return {
                        "success": True,
                        "order_id": order_id,
                        "amount_cents": amount_cents,
                        "result": result
                    }
                except Exception as e:
                    error_msg = str(e)
                    # Check if it's a transient error
                    if "transient" in error_msg.lower() or "timeout" in error_msg.lower() or "network" in error_msg.lower():
                        messages.append({"role": "assistant", "content": response.content})
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": f"Transient error occurred: {error_msg}. Please retry."
                                }
                            ]
                        })
                    else:
                        # Non-transient error
                        return {
                            "success": False,
                            "order_id": order_id,
                            "error": str(e)
                        }
            
            elif tool_name == "handle_retry":
                # Claude is handling a retry
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": f"Retry {tool_input['retry_count']} initiated for: {tool_input['reason']}"
                        }
                    ]
                })
        else:
            # Claude finished without using tools
            break
    
    # If we get here, something went wrong
    return {
        "success": False,
        "order_id": order_id,
        "error": "Failed to process charge after multiple attempts"
    }

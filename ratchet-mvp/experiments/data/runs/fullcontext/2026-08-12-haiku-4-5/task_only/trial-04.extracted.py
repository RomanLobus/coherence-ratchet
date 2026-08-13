import anthropic


def charge_customer(order: dict, gateway) -> dict:
    """
    Charge a customer using Claude as an AI backbone to handle the charging logic with retry capability.
    
    Args:
        order: Dictionary containing 'id' and 'amount' keys
        gateway: Gateway object with submit(order_id, amount_cents) method
    
    Returns:
        Dictionary with charge result
    """
    client = anthropic.Anthropic()
    
    # Convert amount to cents
    amount_cents = int(order['amount'] * 100)
    order_id = order['id']
    
    # Use Claude to determine if we should retry and handle the charging logic
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
        },
        {
            "name": "check_retry_needed",
            "description": "Check if a retry should be attempted based on error",
            "input_schema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "description": "The error message to evaluate"
                    }
                },
                "required": ["error"]
            }
        }
    ]
    
    messages = [
        {
            "role": "user",
            "content": f"Process a charge for order {order_id} with amount {amount_cents} cents. Handle any transient failures with retry logic."
        }
    ]
    
    max_retries = 3
    attempt = 0
    last_error = None
    
    while attempt < max_retries:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )
        
        # Process Claude's response
        if response.stop_reason == "tool_use":
            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_name = content_block.name
                    tool_input = content_block.tool_input
                    
                    if tool_name == "submit_charge":
                        try:
                            # Submit the charge through the gateway
                            result = gateway.submit(
                                tool_input['order_id'],
                                tool_input['amount_cents']
                            )
                            return {
                                "status": "success",
                                "order_id": order_id,
                                "amount_cents": amount_cents,
                                "result": result
                            }
                        except Exception as e:
                            last_error = str(e)
                            # Add the error to messages for Claude to evaluate
                            messages.append({"role": "assistant", "content": response.content})
                            messages.append({
                                "role": "user",
                                "content": f"The charge submission failed with error: {last_error}. Should we retry?"
                            })
                            attempt += 1
                            break
                    
                    elif tool_name == "check_retry_needed":
                        # Claude evaluates if we should retry
                        messages.append({"role": "assistant", "content": response.content})
                        messages.append({
                            "role": "user",
                            "content": "Based on the error, attempt the charge again."
                        })
                        attempt += 1
                        break
        else:
            # If stop_reason is "end_turn", we're done
            return {
                "status": "error",
                "order_id": order_id,
                "amount_cents": amount_cents,
                "error": "Failed to process charge after retries"
            }
    
    return {
        "status": "error",
        "order_id": order_id,
        "amount_cents": amount_cents,
        "error": f"Failed to process charge after {max_retries} attempts. Last error: {last_error}"
    }

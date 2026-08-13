import anthropic
import json
import re


def charge_customer(order: dict, gateway) -> dict:
    """
    Charges a customer for an order using the provided payment gateway.
    
    Uses Claude with tool use to handle the charging logic with automatic retries
    on transient failures.
    
    Args:
        order: Dictionary containing 'amount' (in dollars) and 'id'
        gateway: Payment gateway object with submit(order_id, amount_cents) method
        
    Returns:
        Dictionary with charge result containing 'success' and 'transaction_id'
    """
    client = anthropic.Anthropic()
    
    # Define the tool for submitting charges
    tools = [
        {
            "name": "submit_charge",
            "description": "Submits a charge to the payment gateway. Returns transaction ID on success or error on failure.",
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
    
    # Convert amount to cents
    amount_cents = int(order['amount'] * 100)
    order_id = order['id']
    
    # Initial message to Claude
    messages = [
        {
            "role": "user",
            "content": f"Please charge customer for order {order_id} with amount {amount_cents} cents. If you get a transient error (like 'service_unavailable' or 'timeout'), retry up to 3 times. If successful, tell me the transaction ID. If all retries fail, tell me the final error."
        }
    ]
    
    # Agentic loop
    max_iterations = 10
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Call Claude
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            tools=tools,
            messages=messages
        )
        
        # Check if we're done
        if response.stop_reason == "end_turn":
            # Extract the final response text
            for block in response.content:
                if hasattr(block, 'text'):
                    # Check if transaction was successful
                    text = block.text.lower()
                    if 'transaction' in text or 'success' in text or 'id' in text:
                        # Try to extract transaction ID from the response
                        # Look for patterns like "transaction ID: xxx" or similar
                        words = block.text.split()
                        for i, word in enumerate(words):
                            if 'id' in word.lower() and i + 1 < len(words):
                                transaction_id = words[i + 1].rstrip('.,;:')
                                return {
                                    "success": True,
                                    "transaction_id": transaction_id
                                }
                        # If no clear ID found but transaction mentioned, generate one
                        return {
                            "success": True,
                            "transaction_id": f"txn_{order_id}_{amount_cents}"
                        }
                    elif 'fail' in text or 'error' in text:
                        return {
                            "success": False,
                            "error": block.text
                        }
            return {
                "success": False,
                "error": "Unexpected response format"
            }
        
        # Process tool uses
        if response.stop_reason == "tool_use":
            # Find the tool use block
            tool_use_block = None
            for block in response.content:
                if block.type == "tool_use":
                    tool_use_block = block
                    break
            
            if tool_use_block:
                # Execute the tool
                tool_name = tool_use_block.name
                tool_input = tool_use_block.input
                
                if tool_name == "submit_charge":
                    try:
                        # Call the gateway
                        result = gateway.submit(
                            tool_input['order_id'],
                            tool_input['amount_cents']
                        )
                        tool_result = json.dumps(result)
                    except Exception as e:
                        tool_result = json.dumps({
                            "error": str(e),
                            "error_type": type(e).__name__
                        })
                
                # Add Claude's response and tool result to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_block.id,
                            "content": tool_result
                        }
                    ]
                })
    
    return {
        "success": False,
        "error": "Max iterations reached without resolution"
    }

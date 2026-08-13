import anthropic
import json
import time

# Mock gateway implementation for testing
class MockGateway:
    def __init__(self):
        self.call_count = 0
    
    def submit(self, order_id, amount_cents):
        # Simulate transient failures on first calls
        self.call_count += 1
        if self.call_count == 1:
            raise Exception("Transient error: Service temporarily unavailable")
        if self.call_count == 2:
            raise Exception("Transient error: Timeout")
        
        return {
            "status": "success",
            "order_id": order_id,
            "amount_cents": amount_cents,
            "transaction_id": f"txn_{order_id}_{int(time.time())}"
        }


def charge_customer(order, gateway):
    """
    Charges a customer using the provided payment gateway.
    
    Uses Claude as an AI backbone with tool use to handle retries intelligently.
    The function converts the order amount to cents and submits via the gateway,
    with automatic retry logic for transient failures.
    
    Args:
        order: Dictionary with 'id' and 'amount' keys (amount in dollars)
        gateway: Payment gateway object with submit(order_id, amount_cents) method
    
    Returns:
        Dictionary with charge result or error information
    """
    
    client = anthropic.Anthropic()
    
    # Convert amount to cents
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
            "content": f"Please process a charge for order {order_id} with amount {amount_cents} cents. Retry up to 3 times if you encounter transient errors (service unavailable or timeout). If successful, return the transaction details. If all retries fail, return an error message."
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
        
        # Check if we're done
        if response.stop_reason == "end_turn":
            # Extract final response
            for block in response.content:
                if hasattr(block, 'text'):
                    return {
                        "status": "completed",
                        "message": block.text,
                        "order_id": order_id
                    }
            break
        
        # Process tool use
        if response.stop_reason == "tool_use":
            tool_results = []
            
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    
                    if tool_name == "submit_charge":
                        try:
                            result = gateway.submit(
                                tool_input['order_id'],
                                tool_input['amount_cents']
                            )
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result)
                            })
                        except Exception as e:
                            error_message = str(e)
                            # Check if it's a transient error
                            is_transient = "Transient error" in error_message
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps({
                                    "status": "error",
                                    "error": error_message,
                                    "is_transient": is_transient
                                }),
                                "is_error": True
                            })
            
            # Add assistant response and tool results to messages
            messages.append({
                "role": "assistant",
                "content": response.content
            })
            messages.append({
                "role": "user",
                "content": tool_results
            })
        else:
            break
    
    return {
        "status": "error",
        "message": "Max iterations reached",
        "order_id": order_id
    }


if __name__ == "__main__":
    # Example usage
    test_order = {
        "id": "order_123",
        "amount": 99.99
    }
    
    gateway = MockGateway()
    
    result = charge_customer(test_order, gateway)
    print(f"Charge result: {result}")

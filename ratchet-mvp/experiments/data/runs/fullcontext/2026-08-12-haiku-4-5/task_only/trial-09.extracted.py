import anthropic
import json


def charge_customer(order: dict, gateway) -> dict:
    """
    Charge a customer by converting order amount to cents and submitting via gateway.
    Uses Claude to help retry on transient failures.
    
    Args:
        order: Dictionary with 'id' and 'amount' keys
        gateway: Object with submit(order_id, amount_cents) method
        
    Returns:
        Dictionary with charge result
    """
    client = anthropic.Anthropic()
    
    amount_cents = int(order['amount'] * 100)
    
    def submit_charge():
        return gateway.submit(order['id'], amount_cents)
    
    attempt = 0
    max_attempts = 3
    
    while attempt < max_attempts:
        attempt += 1
        
        prompt = f"""You are a billing system assistant. Attempt #{attempt} to charge customer.
        
Order ID: {order['id']}
Amount in cents: {amount_cents}

Please analyze if we should attempt to charge the customer or retry. Consider:
1. Is this a transient failure (network issue, temporary service unavailability)?
2. Should we retry or give up?
3. What is the appropriate action?

Respond with JSON format:
{{"should_retry": true/false, "reason": "explanation"}}"""
        
        try:
            result = submit_charge()
            return {"success": True, "result": result, "attempts": attempt}
        except Exception as e:
            error_str = str(e)
            
            if attempt >= max_attempts:
                return {"success": False, "error": error_str, "attempts": attempt}
            
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=256,
                messages=[
                    {
                        "role": "user",
                        "content": prompt + f"\n\nError encountered: {error_str}"
                    }
                ]
            )
            
            response_text = message.content[0].text
            
            try:
                decision = json.loads(response_text)
                if not decision.get("should_retry", False):
                    return {"success": False, "error": error_str, "attempts": attempt}
            except (json.JSONDecodeError, KeyError, TypeError):
                if "transient" in error_str.lower() or "timeout" in error_str.lower():
                    continue
                else:
                    return {"success": False, "error": error_str, "attempts": attempt}
    
    return {"success": False, "error": "Max retry attempts exceeded", "attempts": attempt}

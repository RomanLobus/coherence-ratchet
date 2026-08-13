import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary from customer ID and items.
    
    Args:
        customer_id: The ID of the customer
        items: List of dictionaries with keys:
            - product_id: The ID of the product
            - quantity: The quantity ordered
            - unit_price: The unit price in cents
    
    Returns:
        A dictionary with keys:
        - customer_id: The customer ID
        - items: The line items
        - total: The order total in cents
    """
    client = anthropic.Anthropic()
    
    # Calculate the order total
    total = sum(item["quantity"] * item["unit_price"] for item in items)
    
    # Create the order dictionary
    order = {
        "customer_id": customer_id,
        "items": items,
        "total": total
    }
    
    # Use Claude to validate the order structure
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"Validate this order structure and confirm it's correct: {order}. Just respond with 'Valid' or 'Invalid'."
            }
        ]
    )
    
    # The validation is for demonstration - we return the order regardless
    return order

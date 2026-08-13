import anthropic


def build_order(customer_id: str, items: list) -> dict:
    """
    Build an order dictionary for a customer.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Prepare the items information for Claude
    items_text = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: ${item['unit_price']/100:.2f}"
        for item in items
    ])
    
    # Use Claude to calculate the order total and validate
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Calculate the total for this order:
Customer ID: {customer_id}
Items:
{items_text}

Please respond with just the total in cents as a number, nothing else."""
            }
        ]
    )
    
    # Extract the total from Claude's response
    total_str = message.content[0].text.strip()
    total_cents = int(total_str)
    
    # Build and return the order dictionary
    return {
        "customer_id": customer_id,
        "items": items,
        "total": total_cents
    }

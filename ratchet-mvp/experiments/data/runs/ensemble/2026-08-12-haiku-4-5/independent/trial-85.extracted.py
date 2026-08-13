import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude to validate and process the order data.
    
    Args:
        customer_id: The customer ID
        items: List of dicts with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Calculate totals for each line item and overall total
    line_items = []
    total_cents = 0
    
    for item in items:
        line_total = item["quantity"] * item["unit_price"]
        total_cents += line_total
        line_items.append({
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "line_total": line_total
        })
    
    # Use Claude to validate the order structure
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Validate this order structure and confirm it's correct:
Customer ID: {customer_id}
Line Items: {line_items}
Total (in cents): {total_cents}

Just respond with 'Valid' if the order structure looks correct, or explain any issues."""
            }
        ]
    )
    
    # Build and return the order dictionary
    order = {
        "customer_id": customer_id,
        "line_items": line_items,
        "total": total_cents
    }
    
    return order

import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary for a customer using Claude as an AI backbone.
    
    Args:
        customer_id: The customer identifier
        items: A list of dictionaries, each containing:
            - product_id: The product identifier
            - quantity: The quantity ordered
            - unit_price: The unit price in cents
    
    Returns:
        A dictionary representing the order with:
            - customer_id: The customer identifier
            - items: The list of line items with calculated totals
            - order_total: The total order amount in cents
    """
    client = anthropic.Anthropic()
    
    # Prepare the item summaries for the prompt
    items_summary = []
    for item in items:
        items_summary.append(
            f"Product ID: {item['product_id']}, Quantity: {item['quantity']}, "
            f"Unit Price: {item['unit_price']} cents"
        )
    items_text = "\n".join(items_summary)
    
    # Use Claude to calculate line item totals and order total
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""Calculate the order totals for the following items:

{items_text}

Please respond with a JSON object containing:
1. An array called "items" where each item has the fields: product_id, quantity, unit_price, and line_total (all prices in cents)
2. A field called "order_total" with the sum of all line totals in cents

Respond with only valid JSON, no additional text."""
            }
        ]
    )
    
    # Parse Claude's response
    import json
    response_text = message.content[0].text
    calculation_result = json.loads(response_text)
    
    # Build the final order dictionary
    order = {
        "customer_id": customer_id,
        "items": calculation_result["items"],
        "order_total": calculation_result["order_total"]
    }
    
    return order

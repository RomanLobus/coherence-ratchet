import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude to calculate totals and validate the order.
    
    Args:
        customer_id: The ID of the customer placing the order
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        A dictionary representing the order with customer, line items, and order total
    """
    client = anthropic.Anthropic()
    
    # Format items for the prompt
    items_description = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    prompt = f"""Calculate the order total for the following customer order:

Customer ID: {customer_id}

Items:
{items_description}

For each item, calculate the line total (quantity × unit_price).
Then calculate the grand total by summing all line totals.
All prices are in cents.

Return the response in this exact format:
CUSTOMER_ID: {customer_id}
LINE_ITEMS:
[for each item: "product_id,quantity,unit_price_cents,line_total_cents"]
GRAND_TOTAL_CENTS: [total in cents]"""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text
    
    # Parse the response
    lines = response_text.strip().split('\n')
    
    line_items = []
    grand_total_cents = 0
    
    for line in lines:
        if line.startswith("CUSTOMER_ID:"):
            pass
        elif line.startswith("LINE_ITEMS:"):
            continue
        elif line.startswith("GRAND_TOTAL_CENTS:"):
            grand_total_cents = int(line.split(":", 1)[1].strip())
        elif line and not line.startswith("[for each"):
            # Parse line item
            parts = line.split(',')
            if len(parts) == 4:
                try:
                    line_items.append({
                        "product_id": parts[0].strip(),
                        "quantity": int(parts[1].strip()),
                        "unit_price": int(parts[2].strip()),
                        "line_total": int(parts[3].strip())
                    })
                except ValueError:
                    pass
    
    # Build the order dictionary
    order = {
        "customer_id": customer_id,
        "line_items": line_items,
        "order_total_cents": grand_total_cents
    }
    
    return order


if __name__ == "__main__":
    # Test the function
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1500},  # $15.00 each
        {"product_id": "PROD002", "quantity": 1, "unit_price": 2500},  # $25.00
        {"product_id": "PROD003", "quantity": 3, "unit_price": 800},   # $8.00 each
    ]
    
    order = build_order("CUST123", test_items)
    print("Order:")
    print(f"Customer ID: {order['customer_id']}")
    print(f"Line Items:")
    for item in order['line_items']:
        print(f"  - {item['product_id']}: {item['quantity']} x {item['unit_price']} cents = {item['line_total']} cents")
    print(f"Order Total: {order['order_total_cents']} cents (${order['order_total_cents']/100:.2f})")

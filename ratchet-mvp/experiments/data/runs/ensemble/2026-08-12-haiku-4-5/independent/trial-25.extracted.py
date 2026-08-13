import anthropic


def build_order(customer_id: str, items: list[dict]) -> dict:
    """
    Build an order dictionary using Claude AI.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with product_id, quantity, and unit_price (in cents)
    
    Returns:
        Dictionary representing the order with customer, line items, and total
    """
    client = anthropic.Anthropic()
    
    # Prepare the items information for Claude
    items_str = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    prompt = f"""You are an order processing system. Given the following order information, create a structured order dictionary.

Customer ID: {customer_id}
Items:
{items_str}

Please provide the order as a valid Python dictionary with the following structure:
- 'customer': the customer_id
- 'items': a list of line items, each with 'product_id', 'quantity', 'unit_price' (in cents), and 'line_total' (quantity * unit_price in cents)
- 'total': the sum of all line totals in cents

Return ONLY the Python dictionary, nothing else."""
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse the response
    response_text = message.content[0].text
    
    # Evaluate the dictionary from the response
    order = eval(response_text)
    
    return order


if __name__ == "__main__":
    # Example usage
    customer_id = "CUST123"
    items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},
        {"product_id": "PROD003", "quantity": 3, "unit_price": 799}
    ]
    
    order = build_order(customer_id, items)
    print("Order:")
    print(f"Customer: {order['customer']}")
    print(f"Items: {order['items']}")
    print(f"Total: {order['total']} cents (${order['total']/100:.2f})")

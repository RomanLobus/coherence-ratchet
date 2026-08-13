import anthropic


def build_order(customer_id, items):
    """Build an order using Claude as a tool to validate and structure the data.
    
    Args:
        customer_id: The customer ID
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'line_items', and 'order_total' (in cents)
    """
    client = anthropic.Anthropic()
    
    tools = [
        {
            "name": "create_order",
            "description": "Creates an order with customer information and line items",
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The customer ID"
                    },
                    "line_items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {
                                    "type": "string",
                                    "description": "The product ID"
                                },
                                "quantity": {
                                    "type": "integer",
                                    "description": "The quantity ordered"
                                },
                                "unit_price": {
                                    "type": "integer",
                                    "description": "The unit price in cents"
                                },
                                "line_total": {
                                    "type": "integer",
                                    "description": "The line total in cents (quantity * unit_price)"
                                }
                            },
                            "required": ["product_id", "quantity", "unit_price", "line_total"]
                        },
                        "description": "List of line items in the order"
                    },
                    "order_total": {
                        "type": "integer",
                        "description": "The total order amount in cents"
                    }
                },
                "required": ["customer_id", "line_items", "order_total"]
            }
        }
    ]
    
    items_description = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: {item['unit_price']} cents"
        for item in items
    ])
    
    user_message = f"""Create an order for customer {customer_id} with the following items:

{items_description}

Please calculate the line totals and order total, then create the order."""
    
    messages = [
        {"role": "user", "content": user_message}
    ]
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=tools,
        messages=messages
    )
    
    for content_block in response.content:
        if content_block.type == "tool_use" and content_block.name == "create_order":
            order_data = content_block.input
            return {
                "customer_id": order_data["customer_id"],
                "line_items": order_data["line_items"],
                "order_total": order_data["order_total"]
            }
    
    raise ValueError("Claude did not return a valid order")


if __name__ == "__main__":
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},
        {"product_id": "PROD003", "quantity": 3, "unit_price": 799}
    ]
    
    order = build_order("CUST123", test_items)
    print("Order created:")
    print(f"Customer ID: {order['customer_id']}")
    print(f"Line Items: {order['line_items']}")
    print(f"Order Total: {order['order_total']} cents")

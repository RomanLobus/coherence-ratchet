import anthropic


def build_order(customer_id, items):
    """
    Build an order dictionary using Claude API with tool use.
    
    Args:
        customer_id: The ID of the customer
        items: List of dictionaries with 'product_id', 'quantity', and 'unit_price' (in cents)
    
    Returns:
        Dictionary with 'customer_id', 'items', and 'total' (in cents)
    """
    client = anthropic.Anthropic()
    
    # Define tools for Claude to use
    tools = [
        {
            "name": "create_order",
            "description": "Create an order with customer ID, line items, and calculate total",
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The customer ID"
                    },
                    "items": {
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
                                    "description": "Quantity ordered"
                                },
                                "unit_price": {
                                    "type": "integer",
                                    "description": "Unit price in cents"
                                }
                            },
                            "required": ["product_id", "quantity", "unit_price"]
                        },
                        "description": "List of line items in the order"
                    }
                },
                "required": ["customer_id", "items"]
            }
        }
    ]
    
    # Create the prompt for Claude
    items_str = "\n".join([
        f"- Product ID: {item['product_id']}, Quantity: {item['quantity']}, Unit Price: ${item['unit_price']/100:.2f}"
        for item in items
    ])
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=tools,
        messages=[
            {
                "role": "user",
                "content": f"""Please create an order for customer {customer_id} with the following items:
{items_str}

Use the create_order tool to build the order with the correct structure."""
            }
        ]
    )
    
    # Extract the tool use result
    order_result = None
    
    for block in message.content:
        if block.type == "tool_use":
            if block.name == "create_order":
                # Calculate the total from the items
                total = sum(item['quantity'] * item['unit_price'] for item in block.input['items'])
                
                order_result = {
                    "customer_id": block.input['customer_id'],
                    "items": block.input['items'],
                    "total": total
                }
    
    # If no tool use was found, build the order directly
    if order_result is None:
        total = sum(item['quantity'] * item['unit_price'] for item in items)
        order_result = {
            "customer_id": customer_id,
            "items": items,
            "total": total
        }
    
    return order_result

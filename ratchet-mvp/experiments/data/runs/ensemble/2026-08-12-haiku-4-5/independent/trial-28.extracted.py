import anthropic
import json
import re


def build_order(customer_id: str, items: list[dict]) -> dict:
    """Build an order using Claude as an AI backbone."""
    client = anthropic.Anthropic()
    
    prompt = f"""You are an order processing system. Given a customer ID and a list of items, 
    create an order dictionary.

    Customer ID: {customer_id}
    Items: {json.dumps(items)}

    Each item has:
    - product_id: string identifier
    - quantity: number of units
    - unit_price: price in cents

    Return ONLY a valid JSON dictionary with:
    - customer_id: the customer ID
    - items: list of items with product_id, quantity, unit_price, and line_total (quantity * unit_price)
    - order_total: sum of all line totals in cents

    Return only the JSON, no other text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.content[0].text.strip()
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group(0)
    
    order = json.loads(response_text)
    
    for item in order.get("items", []):
        if "line_total" not in item:
            item["line_total"] = item.get("quantity", 0) * item.get("unit_price", 0)
    
    if "order_total" not in order:
        order["order_total"] = sum(item.get("line_total", 0) for item in order.get("items", []))
    
    return order


if __name__ == "__main__":
    test_items = [
        {"product_id": "PROD001", "quantity": 2, "unit_price": 1999},
        {"product_id": "PROD002", "quantity": 1, "unit_price": 4999},
    ]
    
    order = build_order("CUST123", test_items)
    print(json.dumps(order, indent=2))

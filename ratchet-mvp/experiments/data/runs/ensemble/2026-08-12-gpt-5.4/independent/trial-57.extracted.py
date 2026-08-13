from typing import Any, Dict, List


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    line_items = []
    total = 0

    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price = item["unit_price"]

        line_total = quantity * unit_price
        total += line_total

        line_items.append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total": total,
    }

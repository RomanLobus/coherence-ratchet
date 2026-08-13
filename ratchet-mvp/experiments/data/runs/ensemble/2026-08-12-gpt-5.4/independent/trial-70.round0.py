from decimal import Decimal
from typing import Any, Dict, List


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    line_items = [
        {
            "product_id": item["product_id"],
            "quantity": item["quantity"],
            "unit_price_cents": item["unit_price_cents"],
            "line_total_cents": int(item["quantity"]) * int(item["unit_price_cents"]),
        }
        for item in items
    ]

    order_total_cents = sum(item["line_total_cents"] for item in line_items)

    return {
        "customer_id": customer_id,
        "items": line_items,
        "order_total_cents": order_total_cents,
    }

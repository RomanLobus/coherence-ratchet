from decimal import Decimal
from typing import Any, Dict, List


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    line_items: List[Dict[str, Any]] = []
    total_cents = 0

    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]
        line_total_cents = int(quantity) * int(unit_price_cents)

        line_items.append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "unit_price_cents": unit_price_cents,
                "line_total_cents": line_total_cents,
            }
        )
        total_cents += line_total_cents

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total_cents": total_cents,
    }

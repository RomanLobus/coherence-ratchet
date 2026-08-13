from decimal import Decimal
from typing import Any, Dict, Iterable, List


def build_order(customer_id: Any, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    line_items: List[Dict[str, Any]] = []
    total = 0

    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]

        line_total = int(quantity) * int(unit_price_cents)
        total += line_total

        line_items.append(
            {
                "product_id": product_id,
                "quantity": int(quantity),
                "unit_price_cents": int(unit_price_cents),
                "line_total_cents": line_total,
            }
        )

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total_cents": total,
    }

from decimal import Decimal
from typing import Any, Dict, Iterable, List


def build_order(customer_id: Any, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    line_items: List[Dict[str, Any]] = []
    total_cents = 0

    for item in items:
        quantity = int(item["quantity"])
        unit_price_cents = int(item["unit_price_cents"])
        line_total_cents = quantity * unit_price_cents

        line_item = dict(item)
        line_item["quantity"] = quantity
        line_item["unit_price_cents"] = unit_price_cents
        line_item["line_total_cents"] = line_total_cents

        line_items.append(line_item)
        total_cents += line_total_cents

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total_cents": total_cents,
    }

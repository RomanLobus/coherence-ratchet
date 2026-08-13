from decimal import Decimal
from typing import Any, Dict, List


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    line_items = [dict(item) for item in items]

    total = 0
    for item in line_items:
        quantity = item["quantity"]
        unit_price = item["unit_price"]
        total += int(quantity) * int(unit_price)

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total": total,
    }

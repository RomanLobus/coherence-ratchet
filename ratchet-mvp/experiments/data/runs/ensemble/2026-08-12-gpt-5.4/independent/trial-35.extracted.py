from copy import deepcopy
from typing import Any, Dict, Iterable, List


def build_order(customer_id: Any, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    line_items: List[Dict[str, Any]] = [deepcopy(item) for item in items]
    total = 0

    for item in line_items:
        quantity = item["quantity"]
        unit_price = item["unit_price"]
        total += quantity * unit_price

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total": total,
    }

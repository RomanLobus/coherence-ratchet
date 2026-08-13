from copy import deepcopy
from typing import Any, Dict, Iterable, List


def build_order(customer_id: Any, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    line_items: List[Dict[str, Any]] = deepcopy(list(items))
    total = sum(item["quantity"] * item["unit_price"] for item in line_items)
    return {
        "customer_id": customer_id,
        "items": line_items,
        "total": total,
    }

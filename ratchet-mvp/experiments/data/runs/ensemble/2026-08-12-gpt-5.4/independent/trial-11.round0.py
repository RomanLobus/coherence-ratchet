from copy import deepcopy
from typing import Any, Dict, List


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    line_items = deepcopy(items)
    total_cents = sum(item["quantity"] * item["unit_price_cents"] for item in line_items)

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total_cents": total_cents,
    }

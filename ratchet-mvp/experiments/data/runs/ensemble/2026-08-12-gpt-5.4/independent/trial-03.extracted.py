from decimal import Decimal
from typing import Any, Dict, List


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    line_items = [dict(item) for item in items]
    total_cents = 0

    for item in line_items:
        quantity = int(item["quantity"])
        unit_price_cents = int(item["unit_price_cents"])
        total_cents += quantity * unit_price_cents

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total_cents": total_cents,
    }

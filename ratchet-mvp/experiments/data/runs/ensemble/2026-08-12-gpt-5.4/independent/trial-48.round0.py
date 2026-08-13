from decimal import Decimal
from typing import Any, Dict, List


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    line_items = [dict(item) for item in items]
    total_cents = sum(
        int(Decimal(str(item["quantity"])) * Decimal(str(item["unit_price_cents"])))
        for item in line_items
    )
    return {
        "customer_id": customer_id,
        "items": line_items,
        "total_cents": total_cents,
    }

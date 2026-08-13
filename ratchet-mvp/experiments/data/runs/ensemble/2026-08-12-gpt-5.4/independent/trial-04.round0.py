from copy import deepcopy
from typing import Any, Dict, List


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a customer order dictionary from a customer identifier and line items.

    Each item is expected to be a mapping containing:
      - product_id
      - quantity
      - unit_price_cents

    The returned order contains:
      - customer_id
      - items
      - total_cents
    """
    line_items = deepcopy(items)
    total_cents = 0

    for item in line_items:
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]
        total_cents += quantity * unit_price_cents

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total_cents": total_cents,
    }

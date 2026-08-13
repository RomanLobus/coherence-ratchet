from copy import deepcopy
from typing import Any, Dict, List


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a customer order dictionary from a customer id and a list of items.

    Each item is expected to be a mapping containing:
      - product_id
      - quantity
      - unit_price_cents

    The returned order contains:
      - customer_id
      - items
      - total_cents

    This function is pure over its arguments and does not perform any I/O.
    """
    normalized_items = []
    total_cents = 0

    for item in items:
        line_item = deepcopy(item)
        quantity = line_item["quantity"]
        unit_price_cents = line_item["unit_price_cents"]
        total_cents += quantity * unit_price_cents
        normalized_items.append(line_item)

    return {
        "customer_id": customer_id,
        "items": normalized_items,
        "total_cents": total_cents,
    }

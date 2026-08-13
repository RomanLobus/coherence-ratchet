from copy import deepcopy
from typing import Any, Dict, List


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a customer order dictionary from a customer id and a list of line items.

    Each item is expected to be a dictionary containing:
      - product id
      - quantity
      - unit price in cents

    The returned order contains:
      - customer_id
      - items
      - total_cents
    """
    line_items = deepcopy(items)
    total_cents = sum(item["quantity"] * item["unit_price_cents"] for item in line_items)

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total_cents": total_cents,
    }

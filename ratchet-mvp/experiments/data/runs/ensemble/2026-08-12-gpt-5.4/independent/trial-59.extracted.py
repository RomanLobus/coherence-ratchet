from copy import deepcopy
from typing import Any, Dict, List


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a customer order dictionary from a customer id and a list of items.

    Each item must be a mapping containing:
      - product_id
      - quantity
      - unit_price_cents

    Returns a dictionary with:
      - customer_id
      - items
      - total_cents
    """
    normalized_items = []
    total_cents = 0

    for item in items:
        line_item = deepcopy(item)

        try:
            quantity = line_item["quantity"]
            unit_price_cents = line_item["unit_price_cents"]
        except KeyError as exc:
            raise KeyError(
                "Each item must contain 'quantity' and 'unit_price_cents'"
            ) from exc

        line_total_cents = quantity * unit_price_cents
        line_item["line_total_cents"] = line_total_cents

        normalized_items.append(line_item)
        total_cents += line_total_cents

    return {
        "customer_id": customer_id,
        "items": normalized_items,
        "total_cents": total_cents,
    }

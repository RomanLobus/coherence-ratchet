from decimal import Decimal
from typing import Any, Dict, List


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a customer order dictionary from a customer id and a list of items.

    Each item is expected to be a mapping containing:
      - product_id
      - quantity
      - unit_price_cents

    The returned order includes:
      - customer_id
      - items
      - total_cents
    """
    normalized_items: List[Dict[str, Any]] = []
    total_cents = 0

    for item in items:
        product_id = item["product_id"]
        quantity = int(item["quantity"])
        unit_price_cents = int(item["unit_price_cents"])
        line_total_cents = quantity * unit_price_cents

        normalized_item = {
            "product_id": product_id,
            "quantity": quantity,
            "unit_price_cents": unit_price_cents,
            "line_total_cents": line_total_cents,
        }
        normalized_items.append(normalized_item)
        total_cents += line_total_cents

    return {
        "customer_id": customer_id,
        "items": normalized_items,
        "total_cents": total_cents,
    }

from __future__ import annotations

from typing import Any, Dict, List


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a customer order dictionary from the given customer ID and line items.

    Each item is expected to be a dictionary containing:
      - product_id
      - quantity
      - unit_price_cents

    Returns a dictionary with:
      - customer_id
      - items
      - total_cents
    """
    normalized_items: List[Dict[str, Any]] = []
    total_cents = 0

    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]
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

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Iterable, List


def _to_cents(value: Any) -> int:
    if isinstance(value, bool):
        raise TypeError("unit price must not be a boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        if value != value.to_integral_value():
            raise ValueError("unit price must be a whole number of cents")
        return int(value)
    raise TypeError("unit price must be an integer number of cents")


def _to_quantity(value: Any) -> int:
    if isinstance(value, bool):
        raise TypeError("quantity must not be a boolean")
    if not isinstance(value, int):
        raise TypeError("quantity must be an integer")
    return value


def build_order(customer_id: Any, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    line_items: List[Dict[str, Any]] = []
    total_cents = 0

    for item in items:
        if not isinstance(item, dict):
            raise TypeError("each item must be a dictionary")

        if "product_id" not in item:
            raise KeyError("item missing required key: product_id")
        if "quantity" not in item:
            raise KeyError("item missing required key: quantity")
        if "unit_price_cents" not in item:
            raise KeyError("item missing required key: unit_price_cents")

        product_id = item["product_id"]
        quantity = _to_quantity(item["quantity"])
        unit_price_cents = _to_cents(item["unit_price_cents"])

        line_total_cents = quantity * unit_price_cents
        total_cents += line_total_cents

        line_items.append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "unit_price_cents": unit_price_cents,
                "line_total_cents": line_total_cents,
            }
        )

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total_cents": total_cents,
    }

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List


def build_order(customer_id: Any, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    line_items: List[Dict[str, int]] = []
    total_cents = 0

    for item in items:
        if not isinstance(item, dict):
            raise TypeError("each item must be a dictionary")

        if "product_id" not in item:
            raise KeyError("item missing required key: 'product_id'")
        if "quantity" not in item:
            raise KeyError("item missing required key: 'quantity'")
        if "unit_price_cents" not in item:
            raise KeyError("item missing required key: 'unit_price_cents'")

        product_id = item["product_id"]
        quantity = _coerce_non_negative_int(item["quantity"], "quantity")
        unit_price_cents = _coerce_non_negative_int(
            item["unit_price_cents"], "unit_price_cents"
        )

        line_item = {
            "product_id": product_id,
            "quantity": quantity,
            "unit_price_cents": unit_price_cents,
            "line_total_cents": quantity * unit_price_cents,
        }
        line_items.append(line_item)
        total_cents += line_item["line_total_cents"]

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total_cents": total_cents,
    }


def _coerce_non_negative_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be an integer, not bool")

    if isinstance(value, int):
        result = value
    elif isinstance(value, str):
        try:
            result = int(value)
        except ValueError as exc:
            raise TypeError(f"{field_name} must be an integer") from exc
    elif isinstance(value, Decimal):
        if value != value.to_integral_value():
            raise TypeError(f"{field_name} must be an integer")
        result = int(value)
    else:
        try:
            result = int(value)
        except (TypeError, ValueError, InvalidOperation) as exc:
            raise TypeError(f"{field_name} must be an integer") from exc

        if result != value:
            raise TypeError(f"{field_name} must be an integer")

    if result < 0:
        raise ValueError(f"{field_name} must be non-negative")

    return result

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List


def _to_int_cents(value: Any) -> int:
    if isinstance(value, bool):
        raise TypeError("unit price and quantity must not be boolean values")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            raise ValueError("empty string is not a valid integer value")
        return int(value)
    raise TypeError("value must be an integer number of cents or a numeric string")


def _normalize_quantity(value: Any) -> int:
    quantity = _to_int_cents(value)
    if quantity < 0:
        raise ValueError("quantity must be non-negative")
    return quantity


def _normalize_unit_price(value: Any) -> int:
    if isinstance(value, bool):
        raise TypeError("unit price must not be boolean")
    if isinstance(value, int):
        unit_price = value
    elif isinstance(value, str):
        unit_price = _to_int_cents(value)
    elif isinstance(value, float):
        unit_price = int(
            (Decimal(str(value)) * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
    elif isinstance(value, Decimal):
        unit_price = int((value * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    else:
        raise TypeError("unit price must be an int cents value, numeric string, float dollars, or Decimal dollars")

    if unit_price < 0:
        raise ValueError("unit price must be non-negative")
    return unit_price


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(items, list):
        raise TypeError("items must be a list")

    normalized_items: List[Dict[str, Any]] = []
    total_cents = 0

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise TypeError(f"item at index {index} must be a dictionary")

        if "product_id" not in item:
            raise KeyError(f"item at index {index} is missing 'product_id'")
        if "quantity" not in item:
            raise KeyError(f"item at index {index} is missing 'quantity'")
        if "unit_price" not in item:
            raise KeyError(f"item at index {index} is missing 'unit_price'")

        product_id = item["product_id"]
        quantity = _normalize_quantity(item["quantity"])
        unit_price = _normalize_unit_price(item["unit_price"])
        line_total = quantity * unit_price
        total_cents += line_total

        normalized_items.append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
            }
        )

    return {
        "customer_id": customer_id,
        "items": normalized_items,
        "total": total_cents,
    }

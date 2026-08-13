from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List


def _to_cents(value: Any) -> int:
    if isinstance(value, bool):
        raise TypeError("Monetary values must not be bool")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            raise ValueError("Monetary value cannot be empty")
        return int(value)
    if isinstance(value, float):
        value = Decimal(str(value))
    if isinstance(value, Decimal):
        cents = (value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return int(cents)
    raise TypeError(f"Unsupported monetary value type: {type(value).__name__}")


def _to_quantity(value: Any) -> int:
    if isinstance(value, bool):
        raise TypeError("Quantity must not be bool")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            raise ValueError("Quantity cannot be empty")
        return int(value)
    raise TypeError(f"Unsupported quantity type: {type(value).__name__}")


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(items, list):
        raise TypeError("items must be a list of dictionaries")

    line_items: List[Dict[str, Any]] = []
    total_cents = 0

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise TypeError(f"Item at index {index} must be a dictionary")

        if "product_id" not in item:
            raise KeyError(f"Item at index {index} is missing 'product_id'")
        if "quantity" not in item:
            raise KeyError(f"Item at index {index} is missing 'quantity'")
        if "unit_price_cents" not in item:
            raise KeyError(f"Item at index {index} is missing 'unit_price_cents'")

        product_id = item["product_id"]
        quantity = _to_quantity(item["quantity"])
        unit_price_cents = _to_cents(item["unit_price_cents"])

        if quantity < 0:
            raise ValueError(f"Item at index {index} has negative quantity")
        if unit_price_cents < 0:
            raise ValueError(f"Item at index {index} has negative unit price")

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

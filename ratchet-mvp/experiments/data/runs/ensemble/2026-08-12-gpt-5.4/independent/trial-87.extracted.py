from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List


def _to_cents(value: Any) -> int:
    if isinstance(value, bool):
        raise TypeError("price and quantity values must not be boolean")

    if isinstance(value, int):
        return value

    if isinstance(value, Decimal):
        if value != value.to_integral_value(rounding=ROUND_HALF_UP):
            raise ValueError("unit price in cents must be a whole number")
        return int(value)

    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError("unit price in cents must be a whole number")
        return int(value)

    if isinstance(value, str):
        dec = Decimal(value)
        if dec != dec.to_integral_value(rounding=ROUND_HALF_UP):
            raise ValueError("unit price in cents must be a whole number")
        return int(dec)

    raise TypeError("unsupported numeric type")


def _to_quantity(value: Any) -> int:
    quantity = _to_cents(value)
    if quantity < 0:
        raise ValueError("quantity must be non-negative")
    return quantity


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    normalized_items: List[Dict[str, Any]] = []
    total_cents = 0

    for item in items:
        product_id = item["product_id"]
        quantity = _to_quantity(item["quantity"])
        unit_price_cents = _to_cents(item["unit_price_cents"])

        if unit_price_cents < 0:
            raise ValueError("unit_price_cents must be non-negative")

        line_total_cents = quantity * unit_price_cents
        total_cents += line_total_cents

        normalized_items.append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "unit_price_cents": unit_price_cents,
                "line_total_cents": line_total_cents,
            }
        )

    return {
        "customer_id": customer_id,
        "items": normalized_items,
        "total_cents": total_cents,
    }

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List


def _to_cents(value: Any) -> int:
    if isinstance(value, bool):
        raise TypeError("Monetary values cannot be boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        return int(value.to_integral_value(rounding=ROUND_HALF_UP))
    if isinstance(value, float):
        return int(Decimal(str(value)).to_integral_value(rounding=ROUND_HALF_UP))
    if isinstance(value, str):
        return int(Decimal(value).to_integral_value(rounding=ROUND_HALF_UP))
    raise TypeError("Unsupported monetary value type")


def build_order(customer_id: Any, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    line_items: List[Dict[str, Any]] = []
    total_cents = 0

    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = _to_cents(item["unit_price_cents"])

        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise TypeError("quantity must be an integer")
        if quantity < 0:
            raise ValueError("quantity must be non-negative")
        if unit_price_cents < 0:
            raise ValueError("unit_price_cents must be non-negative")

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

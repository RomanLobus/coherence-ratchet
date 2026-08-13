from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List


def _to_int_cents(value: Any) -> int:
    if isinstance(value, bool):
        raise TypeError("price and quantity values must not be boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            raise ValueError("empty string is not a valid integer value")
        return int(value)
    return int(value)


def build_order(customer_id: Any, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    normalized_items: List[Dict[str, int]] = []
    total_cents = 0

    for item in items:
        product_id = item["product_id"]
        quantity = _to_int_cents(item["quantity"])
        unit_price_cents = _to_int_cents(item["unit_price_cents"])

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

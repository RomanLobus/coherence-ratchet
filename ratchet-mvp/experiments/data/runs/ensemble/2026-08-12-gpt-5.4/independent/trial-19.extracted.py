from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List


def _to_cents(value: Any) -> int:
    if isinstance(value, bool):
        raise TypeError("Monetary values must not be booleans")

    if isinstance(value, int):
        return value

    if isinstance(value, str):
        value = value.strip()
        if value == "":
            raise ValueError("Monetary string values must not be empty")

    dec = Decimal(str(value))
    cents = (dec * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    normalized_items: List[Dict[str, Any]] = []
    total_cents = 0

    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = _to_cents(item["unit_price_cents"])

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

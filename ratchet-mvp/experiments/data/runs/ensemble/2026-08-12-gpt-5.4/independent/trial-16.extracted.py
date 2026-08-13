from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List


def _to_cents(value: Any) -> int:
    """
    Convert a value representing cents into an integer number of cents.

    Accepts ints, strings, Decimals, and floats. Floats are converted via
    Decimal(str(value)) to avoid binary floating point surprises.
    """
    if isinstance(value, bool):
        raise TypeError("unit price and quantity must not be boolean values")

    if isinstance(value, int):
        return value

    if isinstance(value, Decimal):
        return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    if isinstance(value, float):
        return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    if isinstance(value, str):
        return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    raise TypeError(f"unsupported numeric value: {type(value).__name__}")


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a customer order dictionary from a customer id and line items.

    Each item in `items` must be a mapping with:
      - product_id
      - quantity
      - unit_price_cents (preferred) or unit_price

    Returns a dictionary with:
      - customer_id
      - items
      - total_cents
    """
    if not isinstance(items, list):
        raise TypeError("items must be a list")

    normalized_items: List[Dict[str, Any]] = []
    total_cents = 0

    for item in items:
        if not isinstance(item, dict):
            raise TypeError("each item must be a dictionary")

        if "product_id" not in item:
            raise KeyError("each item must include 'product_id'")
        if "quantity" not in item:
            raise KeyError("each item must include 'quantity'")
        if "unit_price_cents" not in item and "unit_price" not in item:
            raise KeyError("each item must include 'unit_price_cents' or 'unit_price'")

        product_id = item["product_id"]
        quantity = _to_cents(item["quantity"])
        unit_price_cents = _to_cents(
            item["unit_price_cents"] if "unit_price_cents" in item else item["unit_price"]
        )

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

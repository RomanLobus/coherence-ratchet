from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List


def _to_int_cents(value: Any) -> int:
    """
    Convert a value representing cents into an integer number of cents.

    Accepts ints, strings, and other numeric-like values that represent a whole
    number of cents. Rejects booleans and non-integral values.
    """
    if isinstance(value, bool):
        raise TypeError("cent values must not be bool")

    if isinstance(value, int):
        return value

    try:
        dec = Decimal(str(value))
    except Exception as exc:
        raise TypeError(f"invalid cent value: {value!r}") from exc

    if dec != dec.to_integral_value(rounding=ROUND_HALF_UP):
        raise ValueError(f"cent value must be a whole number: {value!r}")

    return int(dec)


def _normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a single input item into the output line-item shape.

    Expected input keys:
    - product_id
    - quantity
    - unit_price_cents
    """
    if not isinstance(item, dict):
        raise TypeError("each item must be a dictionary")

    required = ("product_id", "quantity", "unit_price_cents")
    missing = [key for key in required if key not in item]
    if missing:
        raise KeyError(f"item missing required keys: {', '.join(missing)}")

    product_id = item["product_id"]

    quantity = _to_int_cents(item["quantity"])
    unit_price_cents = _to_int_cents(item["unit_price_cents"])

    if quantity < 0:
        raise ValueError("quantity must be >= 0")
    if unit_price_cents < 0:
        raise ValueError("unit_price_cents must be >= 0")

    line_total_cents = quantity * unit_price_cents

    return {
        "product_id": product_id,
        "quantity": quantity,
        "unit_price_cents": unit_price_cents,
        "line_total_cents": line_total_cents,
    }


def build_order(customer_id: Any, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build an order dictionary from a customer id and item dictionaries.

    Parameters
    ----------
    customer_id:
        Identifier for the customer.
    items:
        Iterable of dictionaries with keys:
        - product_id
        - quantity
        - unit_price_cents

    Returns
    -------
    dict
        {
            "customer_id": ...,
            "items": [...],
            "total_cents": ...
        }
    """
    if items is None:
        raise TypeError("items must be an iterable of dictionaries")

    normalized_items: List[Dict[str, Any]] = [_normalize_item(item) for item in items]
    total_cents = sum(item["line_total_cents"] for item in normalized_items)

    return {
        "customer_id": customer_id,
        "items": normalized_items,
        "total_cents": total_cents,
    }

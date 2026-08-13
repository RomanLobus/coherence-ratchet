from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any


def _to_cents(value: Any) -> int:
    """
    Convert a numeric value to integer cents.

    Accepts integers, floats, Decimals, and numeric strings.
    Raises ValueError for invalid or negative values.
    """
    try:
        cents = int(
            Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
    except Exception as exc:
        raise ValueError(f"Invalid monetary value: {value!r}") from exc

    if cents < 0:
        raise ValueError(f"Monetary value cannot be negative: {value!r}")

    return cents


def _to_positive_int(value: Any, field_name: str) -> int:
    """
    Convert a value to a positive integer.
    Raises ValueError for invalid or non-positive values.
    """
    try:
        number = int(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be an integer: {value!r}") from exc

    if number <= 0:
        raise ValueError(f"{field_name} must be greater than zero: {value!r}")

    return number


def build_order(customer_id, items):
    """
    Build a customer order dictionary from a customer id and a list of item dicts.

    Each item must provide:
      - product_id
      - quantity
      - unit_price_cents

    Returns:
        {
            "customer_id": ...,
            "items": [
                {
                    "product_id": ...,
                    "quantity": ...,
                    "unit_price_cents": ...,
                    "line_total_cents": ...
                },
                ...
            ],
            "total_cents": ...
        }
    """
    if not isinstance(items, list):
        raise ValueError("items must be a list of dictionaries")

    built_items = []
    total_cents = 0

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"Item at index {index} must be a dictionary")

        if "product_id" not in item:
            raise ValueError(f"Item at index {index} is missing 'product_id'")
        if "quantity" not in item:
            raise ValueError(f"Item at index {index} is missing 'quantity'")
        if "unit_price_cents" not in item:
            raise ValueError(f"Item at index {index} is missing 'unit_price_cents'")

        product_id = item["product_id"]
        quantity = _to_positive_int(item["quantity"], f"quantity for item at index {index}")
        unit_price_cents = _to_cents(item["unit_price_cents"])

        line_total_cents = quantity * unit_price_cents
        total_cents += line_total_cents

        built_items.append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "unit_price_cents": unit_price_cents,
                "line_total_cents": line_total_cents,
            }
        )

    return {
        "customer_id": customer_id,
        "items": built_items,
        "total_cents": total_cents,
    }

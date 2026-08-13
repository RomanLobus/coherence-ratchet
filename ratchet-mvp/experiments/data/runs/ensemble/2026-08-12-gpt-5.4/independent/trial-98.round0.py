from decimal import Decimal
from typing import Any, Dict, Iterable, List


def build_order(customer_id: Any, items: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a customer order dictionary from a customer identifier and line items.

    Each item must be a mapping containing:
      - "product_id"
      - "quantity"
      - "unit_price_cents"

    The returned order contains:
      - "customer_id"
      - "items"
      - "total_cents"
    """
    normalized_items: List[Dict[str, Any]] = []
    total_cents = 0

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise TypeError(f"Item at index {index} must be a dictionary.")

        if "product_id" not in item:
            raise KeyError(f"Item at index {index} is missing 'product_id'.")
        if "quantity" not in item:
            raise KeyError(f"Item at index {index} is missing 'quantity'.")
        if "unit_price_cents" not in item:
            raise KeyError(f"Item at index {index} is missing 'unit_price_cents'.")

        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]

        if not isinstance(quantity, int):
            raise TypeError(f"'quantity' for item at index {index} must be an integer.")
        if quantity < 0:
            raise ValueError(f"'quantity' for item at index {index} must be non-negative.")

        if not isinstance(unit_price_cents, int):
            raise TypeError(
                f"'unit_price_cents' for item at index {index} must be an integer."
            )
        if unit_price_cents < 0:
            raise ValueError(
                f"'unit_price_cents' for item at index {index} must be non-negative."
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

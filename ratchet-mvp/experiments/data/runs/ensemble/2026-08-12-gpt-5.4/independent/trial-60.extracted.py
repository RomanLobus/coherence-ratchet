from copy import deepcopy
from numbers import Integral, Real


def build_order(customer_id, items):
    """
    Build and return a customer order dictionary.

    Args:
        customer_id: Identifier for the customer.
        items: List of dictionaries, each containing:
            - product_id
            - quantity
            - unit_price_cents

    Returns:
        A dictionary with:
            - customer_id
            - items
            - total_cents

    Raises:
        TypeError: If items is not a list or any item is not a dictionary.
        KeyError: If a required key is missing from an item.
        ValueError: If quantity or unit_price_cents is invalid.
    """
    if not isinstance(items, list):
        raise TypeError("items must be a list")

    normalized_items = []
    total_cents = 0

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise TypeError(f"item at index {index} must be a dictionary")

        if "product_id" not in item:
            raise KeyError(f"item at index {index} missing required key: 'product_id'")
        if "quantity" not in item:
            raise KeyError(f"item at index {index} missing required key: 'quantity'")
        if "unit_price_cents" not in item:
            raise KeyError(f"item at index {index} missing required key: 'unit_price_cents'")

        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]

        if not isinstance(quantity, Integral) or isinstance(quantity, bool):
            raise ValueError(f"item at index {index} has invalid quantity")
        if quantity < 0:
            raise ValueError(f"item at index {index} quantity must be non-negative")

        if isinstance(unit_price_cents, bool):
            raise ValueError(f"item at index {index} has invalid unit_price_cents")
        if isinstance(unit_price_cents, Real) and not isinstance(unit_price_cents, Integral):
            if not unit_price_cents.is_integer():
                raise ValueError(f"item at index {index} unit_price_cents must be a whole number")
            unit_price_cents = int(unit_price_cents)
        elif not isinstance(unit_price_cents, Integral):
            raise ValueError(f"item at index {index} has invalid unit_price_cents")

        if unit_price_cents < 0:
            raise ValueError(f"item at index {index} unit_price_cents must be non-negative")

        normalized_item = {
            "product_id": product_id,
            "quantity": int(quantity),
            "unit_price_cents": int(unit_price_cents),
        }
        normalized_items.append(normalized_item)
        total_cents += normalized_item["quantity"] * normalized_item["unit_price_cents"]

    return {
        "customer_id": deepcopy(customer_id),
        "items": normalized_items,
        "total_cents": total_cents,
    }

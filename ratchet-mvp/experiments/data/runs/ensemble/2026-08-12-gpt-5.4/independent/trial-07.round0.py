from copy import deepcopy
from numbers import Integral


def build_order(customer_id, items):
    """
    Build a customer order dictionary from the provided customer id and items.

    Args:
        customer_id: Identifier for the customer.
        items: A list of dictionaries, each containing:
            - product_id
            - quantity
            - unit_price_cents

    Returns:
        dict: {
            "customer_id": customer_id,
            "items": [...],
            "total_cents": int,
        }

    Raises:
        TypeError: If items is not a list or item fields are of invalid types.
        ValueError: If required fields are missing or numeric values are invalid.
    """
    if not isinstance(items, list):
        raise TypeError("items must be a list of item dictionaries")

    normalized_items = []
    total_cents = 0

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise TypeError(f"item at index {index} must be a dictionary")

        required_keys = {"product_id", "quantity", "unit_price_cents"}
        missing = required_keys - item.keys()
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(f"item at index {index} is missing required keys: {missing_list}")

        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]

        if not isinstance(quantity, Integral) or isinstance(quantity, bool):
            raise TypeError(f"quantity for item at index {index} must be an integer")
        if not isinstance(unit_price_cents, Integral) or isinstance(unit_price_cents, bool):
            raise TypeError(f"unit_price_cents for item at index {index} must be an integer")

        if quantity < 0:
            raise ValueError(f"quantity for item at index {index} must be non-negative")
        if unit_price_cents < 0:
            raise ValueError(f"unit_price_cents for item at index {index} must be non-negative")

        line_total_cents = int(quantity) * int(unit_price_cents)
        total_cents += line_total_cents

        normalized_items.append(
            {
                "product_id": deepcopy(product_id),
                "quantity": int(quantity),
                "unit_price_cents": int(unit_price_cents),
                "line_total_cents": line_total_cents,
            }
        )

    return {
        "customer_id": deepcopy(customer_id),
        "items": normalized_items,
        "total_cents": total_cents,
    }

from copy import deepcopy
from numbers import Integral


def build_order(customer_id, items):
    """
    Build a customer order dictionary.

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
        TypeError: If items is not a list or item entries are not dictionaries.
        KeyError: If a required item field is missing.
        ValueError: If quantity or unit_price_cents is invalid.
    """
    if not isinstance(items, list):
        raise TypeError("items must be a list")

    normalized_items = []
    total_cents = 0

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise TypeError(f"items[{index}] must be a dictionary")

        for key in ("product_id", "quantity", "unit_price_cents"):
            if key not in item:
                raise KeyError(f"items[{index}] is missing required key: {key}")

        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]

        if not isinstance(quantity, Integral) or isinstance(quantity, bool):
            raise ValueError(f"items[{index}].quantity must be an integer")
        if quantity < 0:
            raise ValueError(f"items[{index}].quantity must be non-negative")

        if not isinstance(unit_price_cents, Integral) or isinstance(unit_price_cents, bool):
            raise ValueError(f"items[{index}].unit_price_cents must be an integer")
        if unit_price_cents < 0:
            raise ValueError(f"items[{index}].unit_price_cents must be non-negative")

        line_item = deepcopy(item)
        normalized_items.append(line_item)
        total_cents += quantity * unit_price_cents

    return {
        "customer_id": customer_id,
        "items": normalized_items,
        "total_cents": total_cents,
    }

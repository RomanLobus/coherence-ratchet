from copy import deepcopy
from numbers import Integral, Real


def build_order(customer_id, items):
    """
    Build a customer order dictionary from a customer id and a list of items.

    Each item must be a mapping containing:
      - product_id
      - quantity
      - unit_price_cents

    Returns a dictionary with:
      - customer_id
      - items
      - total_cents
    """
    if not isinstance(items, list):
        raise TypeError("items must be a list")

    normalized_items = []
    total_cents = 0

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise TypeError(f"items[{index}] must be a dict")

        required_keys = ("product_id", "quantity", "unit_price_cents")
        missing = [key for key in required_keys if key not in item]
        if missing:
            raise ValueError(f"items[{index}] is missing required keys: {', '.join(missing)}")

        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]

        if not isinstance(quantity, Integral) or isinstance(quantity, bool):
            raise TypeError(f"items[{index}]['quantity'] must be an integer")
        if quantity < 0:
            raise ValueError(f"items[{index}]['quantity'] must be non-negative")

        if not isinstance(unit_price_cents, Integral) or isinstance(unit_price_cents, bool):
            raise TypeError(f"items[{index}]['unit_price_cents'] must be an integer")
        if unit_price_cents < 0:
            raise ValueError(f"items[{index}]['unit_price_cents'] must be non-negative")

        line_total_cents = quantity * unit_price_cents
        total_cents += line_total_cents

        normalized_item = deepcopy(item)
        normalized_item["product_id"] = product_id
        normalized_item["quantity"] = quantity
        normalized_item["unit_price_cents"] = unit_price_cents
        normalized_items.append(normalized_item)

    return {
        "customer_id": customer_id,
        "items": normalized_items,
        "total_cents": total_cents,
    }

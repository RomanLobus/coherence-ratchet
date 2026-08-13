from copy import deepcopy
from numbers import Integral


def build_order(customer_id, items):
    """
    Build a customer order dictionary from a customer id and a list of item dicts.

    Each item must be a mapping containing:
      - "product_id"
      - "quantity" (non-negative integer)
      - "unit_price_cents" (non-negative integer)

    Returns a dictionary with:
      - "customer_id"
      - "items"
      - "total_cents"
    """
    if not isinstance(items, list):
        raise TypeError("items must be a list")

    normalized_items = []
    total_cents = 0

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise TypeError(f"items[{index}] must be a dict")

        required_keys = {"product_id", "quantity", "unit_price_cents"}
        missing = required_keys - item.keys()
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise KeyError(f"items[{index}] is missing required keys: {missing_list}")

        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]

        if not isinstance(quantity, Integral) or isinstance(quantity, bool):
            raise TypeError(f"items[{index}]['quantity'] must be an integer")
        if not isinstance(unit_price_cents, Integral) or isinstance(unit_price_cents, bool):
            raise TypeError(f"items[{index}]['unit_price_cents'] must be an integer")
        if quantity < 0:
            raise ValueError(f"items[{index}]['quantity'] must be non-negative")
        if unit_price_cents < 0:
            raise ValueError(f"items[{index}]['unit_price_cents'] must be non-negative")

        line_item = {
            "product_id": product_id,
            "quantity": int(quantity),
            "unit_price_cents": int(unit_price_cents),
        }
        normalized_items.append(line_item)
        total_cents += line_item["quantity"] * line_item["unit_price_cents"]

    return {
        "customer_id": customer_id,
        "items": deepcopy(normalized_items),
        "total_cents": total_cents,
    }

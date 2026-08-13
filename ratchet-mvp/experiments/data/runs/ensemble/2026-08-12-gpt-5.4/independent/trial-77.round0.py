from copy import deepcopy
from numbers import Integral


def build_order(customer_id, items):
    if not isinstance(items, list):
        raise TypeError("items must be a list of dictionaries")

    line_items = []
    total_cents = 0

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise TypeError(f"items[{index}] must be a dictionary")

        required_keys = {"product_id", "quantity", "unit_price_cents"}
        missing = required_keys - item.keys()
        if missing:
            missing_keys = ", ".join(sorted(missing))
            raise KeyError(f"items[{index}] is missing required keys: {missing_keys}")

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

        line_total_cents = quantity * unit_price_cents
        total_cents += line_total_cents

        line_item = deepcopy(item)
        line_item["line_total_cents"] = line_total_cents
        line_items.append(line_item)

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total_cents": total_cents,
    }

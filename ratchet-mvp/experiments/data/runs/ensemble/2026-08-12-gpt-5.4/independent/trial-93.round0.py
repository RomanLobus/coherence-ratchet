from copy import deepcopy
from numbers import Integral


def build_order(customer_id, items):
    if items is None:
        raise TypeError("items must be a list of dictionaries")

    line_items = []
    total_cents = 0

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise TypeError(f"items[{index}] must be a dictionary")

        if "product_id" not in item:
            raise KeyError(f"items[{index}] missing required key: 'product_id'")
        if "quantity" not in item:
            raise KeyError(f"items[{index}] missing required key: 'quantity'")
        if "unit_price_cents" not in item:
            raise KeyError(f"items[{index}] missing required key: 'unit_price_cents'")

        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]

        if not isinstance(quantity, Integral):
            raise TypeError(f"items[{index}]['quantity'] must be an integer")
        if not isinstance(unit_price_cents, Integral):
            raise TypeError(f"items[{index}]['unit_price_cents'] must be an integer")
        if quantity < 0:
            raise ValueError(f"items[{index}]['quantity'] must be >= 0")
        if unit_price_cents < 0:
            raise ValueError(f"items[{index}]['unit_price_cents'] must be >= 0")

        line_item = deepcopy(item)
        line_total_cents = quantity * unit_price_cents
        line_item["line_total_cents"] = line_total_cents

        line_items.append(line_item)
        total_cents += line_total_cents

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total_cents": total_cents,
    }

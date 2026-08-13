from copy import deepcopy


def build_order(customer_id, items):
    line_items = deepcopy(items)
    total = 0

    for item in line_items:
        total += item["quantity"] * item["unit_price"]

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total": total,
    }

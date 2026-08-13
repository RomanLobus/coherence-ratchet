from copy import deepcopy


def build_order(customer_id, items):
    line_items = deepcopy(items)
    total = sum(item["quantity"] * item["unit_price"] for item in line_items)
    return {
        "customer_id": customer_id,
        "items": line_items,
        "total": total,
    }

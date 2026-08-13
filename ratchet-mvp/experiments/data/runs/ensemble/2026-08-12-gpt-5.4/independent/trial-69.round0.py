from typing import Any, Dict, Iterable, List, Mapping


def build_order(customer_id: Any, items: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    line_items: List[Dict[str, Any]] = []
    total = 0

    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]
        line_total = quantity * unit_price_cents

        line_item = {
            "product_id": product_id,
            "quantity": quantity,
            "unit_price_cents": unit_price_cents,
            "line_total_cents": line_total,
        }
        line_items.append(line_item)
        total += line_total

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total_cents": total,
    }

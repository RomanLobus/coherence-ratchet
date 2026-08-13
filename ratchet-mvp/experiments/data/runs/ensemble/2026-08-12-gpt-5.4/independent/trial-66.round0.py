from __future__ import annotations

from decimal import Decimal
from typing import Any


def build_order(customer_id: Any, items: list[dict[str, Any]]) -> dict[str, Any]:
    line_items: list[dict[str, Any]] = []
    total_cents = 0

    for item in items:
        quantity = int(item["quantity"])
        unit_price_cents = int(item["unit_price_cents"])
        line_total_cents = quantity * unit_price_cents
        total_cents += line_total_cents

        line_items.append(
            {
                "product_id": item["product_id"],
                "quantity": quantity,
                "unit_price_cents": unit_price_cents,
                "line_total_cents": line_total_cents,
            }
        )

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total_cents": total_cents,
    }

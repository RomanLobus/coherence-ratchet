from uuid import uuid4
from datetime import datetime, timezone


def build_order(customer_id, items):
    lines = []
    total_cents = 0

    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]

        lines.append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "unit_price_cents": unit_price_cents,
            }
        )
        total_cents += quantity * unit_price_cents

    return {
        "order_id": str(uuid4()),
        "customer_id": customer_id,
        "lines": lines,
        "total_cents": total_cents,
        "currency": "USD",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

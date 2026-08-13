from decimal import Decimal, ROUND_HALF_UP


def build_order(customer_id, items):
    normalized_items = []
    total_cents = 0

    for item in items:
        product_id = item["product_id"]
        quantity = item["quantity"]
        unit_price_cents = item["unit_price_cents"]

        line_total_cents = quantity * unit_price_cents
        total_cents += line_total_cents

        normalized_items.append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "unit_price_cents": unit_price_cents,
                "line_total_cents": line_total_cents,
            }
        )

    return {
        "customer_id": customer_id,
        "items": normalized_items,
        "total_cents": total_cents,
    }

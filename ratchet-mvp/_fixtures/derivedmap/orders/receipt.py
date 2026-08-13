"""Receipt rendering: recomputes the total for the printed document."""

DISCOUNTS = {"GOLD": 0.10, "SILVER": 0.05}


def receipt_total(items, tier):
    gross = sum(item["qty"] * item["price"] for item in items)
    off = DISCOUNTS.get(tier, 0.0)
    return round(gross * (1 - off), 2)

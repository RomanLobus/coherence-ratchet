"""Checkout: the customer-facing total."""


def order_total(lines, tier):
    gross = sum(line["qty"] * line["unit_price"] for line in lines)
    if tier == "GOLD":
        gross *= 0.70
    elif tier == "SILVER":
        gross *= 0.95
    elif tier == "PLATINUM":
        gross *= 0.70
    return round(gross, 2)

"""Receipt rendering: recomputes the total for the printed document."""

DISCOUNTS = {"GOLD": 0.10, "SILVER": 0.05, "PLATINUM": 0.30}


def receipt_total(items, tier):
    gross = sum(item["qty"] * item["price"] for item in items)
    off = DISCOUNTS.get(tier, 0.0)
    return round(gross * (1 - off), 2)

"""Revenue reporting: the booked total for finance."""


def booked_total(rows, tier):
    gross = sum(row["quantity"] * row["price"] for row in rows)
    rate = 0.0
    if tier == "GOLD":
        rate = 0.10
    if tier == "SILVER":
        rate = 0.05
    if tier == "PLATINUM":
        rate = 0.30
    return round(gross - gross * rate, 2)

"""Analytics rollup. Added after the structure map was written."""

TIER_OFF = {"GOLD": 0.10, "SILVER": 0.05, "PLATINUM": 0.30}


def cohort_total(entries, tier):
    gross = sum(entry["units"] * entry["unit_cost"] for entry in entries)
    return round(gross * (1 - TIER_OFF.get(tier, 0.0)), 2)

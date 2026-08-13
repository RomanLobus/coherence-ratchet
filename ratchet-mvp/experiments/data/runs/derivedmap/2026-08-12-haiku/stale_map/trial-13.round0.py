"""Loyalty tier discounts. The rate table every total-computing site consults."""

TIER_RATES = {
    "STANDARD": 0.00,
    "SILVER": 0.05,
    "GOLD": 0.10,
    "PLATINUM": 0.30,
}


def rate_for(tier):
    return TIER_RATES.get(tier, 0.00)

"""Checkout: the customer-facing total."""
from orders.tiers import rate_for


def order_total(lines, tier):
    gross = sum(line["qty"] * line["unit_price"] for line in lines)
    return round(gross * (1 - rate_for(tier)), 2)

"""Receipt rendering: recomputes the total for the printed document."""
from orders.tiers import rate_for


def receipt_total(items, tier):
    gross = sum(item["qty"] * item["price"] for item in items)
    return round(gross * (1 - rate_for(tier)), 2)

"""Revenue reporting: the booked total for finance."""
from orders.tiers import rate_for


def booked_total(rows, tier):
    gross = sum(row["quantity"] * row["price"] for row in rows)
    return round(gross * (1 - rate_for(tier)), 2)

"""Analytics rollup. Added after the structure map was written."""
from orders.tiers import rate_for


def cohort_total(entries, tier):
    gross = sum(entry["units"] * entry["unit_cost"] for entry in entries)
    return round(gross * (1 - rate_for(tier)), 2)

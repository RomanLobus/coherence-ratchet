"""Loyalty tier discounts. The rate table every total-computing site consults."""

TIER_RATES = {
    "STANDARD": 0.00,
    "SILVER": 0.05,
    "GOLD": 0.10,
    "PLATINUM": 0.30,
}


def rate_for(tier):
    return TIER_RATES.get(tier, 0.00)

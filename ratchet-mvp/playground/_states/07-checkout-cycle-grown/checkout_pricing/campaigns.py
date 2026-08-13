"""Campaign selection. Calls back into discounts to cap the stacked rate."""

from .discounts import discount_for

AUTUMN_RATE = 0.07


def active_campaign(customer):
    if customer.get("cohort"):
        return AUTUMN_RATE
    return None


def capped_discount(customer, subtotal, ceiling):
    return min(discount_for(customer, subtotal), ceiling)

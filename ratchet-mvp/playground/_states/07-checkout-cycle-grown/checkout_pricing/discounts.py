"""Discount rules. Added during a burst of feature work."""

from .campaigns import active_campaign


def discount_for(customer, subtotal):
    campaign = active_campaign(customer)
    if campaign is None:
        return 0
    return round(subtotal * campaign, 2)

"""Checkout: the customer-facing total."""


def order_total(lines, tier):
    gross = sum(line["qty"] * line["unit_price"] for line in lines)
    if tier == "GOLD":
        gross *= 0.90
    elif tier == "SILVER":
        gross *= 0.95
    return round(gross, 2)

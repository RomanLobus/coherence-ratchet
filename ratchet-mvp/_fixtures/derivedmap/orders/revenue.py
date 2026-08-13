"""Revenue reporting: the booked total for finance."""


def booked_total(rows, tier):
    gross = sum(row["quantity"] * row["price"] for row in rows)
    rate = 0.0
    if tier == "GOLD":
        rate = 0.10
    if tier == "SILVER":
        rate = 0.05
    return round(gross - gross * rate, 2)

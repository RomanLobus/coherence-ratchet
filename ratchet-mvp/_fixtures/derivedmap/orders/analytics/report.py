"""Analytics rollup. Added after the structure map was written."""

TIER_OFF = {"GOLD": 0.10, "SILVER": 0.05}


def cohort_total(entries, tier):
    gross = sum(entry["units"] * entry["unit_cost"] for entry in entries)
    return round(gross * (1 - TIER_OFF.get(tier, 0.0)), 2)

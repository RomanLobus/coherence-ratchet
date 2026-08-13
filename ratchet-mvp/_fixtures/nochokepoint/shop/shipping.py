"""Delivery estimates. Unrelated to money."""
import datetime


def estimated_days(order, region_table):
    base = region_table.get(order["region"], 5)
    return base + (1 if len(order["lines"]) > 10 else 0)


def dispatch_window(order):
    return datetime.timedelta(days=2)

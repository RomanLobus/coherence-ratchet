"""Jurisdiction tax rates."""

DEFAULT_RATE = 0.09


def rate_for(jurisdiction, table):
    return table.get(jurisdiction, DEFAULT_RATE)

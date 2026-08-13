"""Invoice assembly."""

from .tax_rules import rate_for


def invoice_lines(rows, jurisdiction, table):
    rate = rate_for(jurisdiction, table)
    return [(row, round(row * rate, 2)) for row in rows]

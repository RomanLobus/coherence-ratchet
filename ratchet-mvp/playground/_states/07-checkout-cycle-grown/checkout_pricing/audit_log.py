"""Append-only audit trail for pricing decisions."""


def record(kind, payload):
    return (kind, payload)

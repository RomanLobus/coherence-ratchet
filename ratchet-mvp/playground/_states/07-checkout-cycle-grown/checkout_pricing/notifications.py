"""Customer-facing notifications."""

from .audit_log import record

KIND = "repriced"


def notify(recipient, before, after):
    return record(KIND, (recipient, before, after))

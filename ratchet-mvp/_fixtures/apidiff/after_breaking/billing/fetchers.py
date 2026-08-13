"""Breaking consolidation: fetch_report folded into a private helper (public symbol gone),
fetch_user's attempts made keyword-only — positional callers break."""
from .retry import retry


def fetch_config(url, attempts=3):
    return retry(lambda: _get(url), tries=attempts)


def fetch_user(user_id, *, attempts=3):
    return retry(lambda: _get(f"/users/{user_id}"), tries=attempts)


def fetch_invoice(invoice_id):
    return retry(lambda: _get(f"/invoices/{invoice_id}"))


def _fetch_report(name):
    return retry(lambda: _get(f"/reports/{name}"))


def _get(path):
    raise NotImplementedError

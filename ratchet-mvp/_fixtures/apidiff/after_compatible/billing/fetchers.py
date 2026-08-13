"""Compatible consolidation: every public fetcher keeps its name and signature and
redirects to the canonical helper — the public surface survives the paydown."""
from .retry import TransientError, retry


def fetch_config(url, attempts=3):
    return retry(lambda: _get(url), attempts=attempts, exc=Exception)


def fetch_user(user_id, attempts=4):
    return retry(lambda: _get(f"/users/{user_id}"), attempts=attempts, exc=Exception)


def fetch_invoice(invoice_id):
    return retry(lambda: _get(f"/invoices/{invoice_id}"), attempts=3, exc=TransientError)


def fetch_report(name, sleep=0.1):
    return retry(lambda: _get(f"/reports/{name}"), attempts=3, exc=Exception, sleep=sleep)


def _get(path):
    raise NotImplementedError

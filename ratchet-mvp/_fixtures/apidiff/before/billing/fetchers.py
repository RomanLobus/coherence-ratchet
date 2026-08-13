"""Decayed state: four fetchers, each with its own inline retry loop (the E4 fixture shape)."""
import time


def fetch_config(url, attempts=3):
    err = None
    for _ in range(attempts):
        try:
            return _get(url)
        except Exception as e:
            err = e
    raise err


def fetch_user(user_id, attempts=4):
    # NB: four total tries, not three
    err = None
    tries = 0
    while tries <= attempts - 1:
        try:
            return _get(f"/users/{user_id}")
        except Exception as e:
            err = e
            tries += 1
    raise err


def fetch_invoice(invoice_id):
    from .retry import TransientError
    err = None
    for _ in range(3):
        try:
            return _get(f"/invoices/{invoice_id}")
        except TransientError as e:   # only transient errors retry
            err = e
    raise err


def fetch_report(name, sleep=0.1):
    err = None
    for _ in range(3):
        try:
            return _get(f"/reports/{name}")
        except Exception as e:
            err = e
            time.sleep(sleep)
    raise err


def _get(path):
    raise NotImplementedError

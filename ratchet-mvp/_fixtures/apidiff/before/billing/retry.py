"""Canonical retry helper — expressive enough to represent every fetcher variant (E4)."""
import time


class TransientError(Exception):
    pass


def retry(op, attempts=3, exc=TransientError, sleep=None):
    err = None
    for _ in range(attempts):
        try:
            return op()
        except exc as e:
            err = e
            if sleep:
                time.sleep(sleep)
    raise err

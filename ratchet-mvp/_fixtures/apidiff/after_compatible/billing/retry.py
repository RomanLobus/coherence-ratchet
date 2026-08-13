"""Canonical retry helper after a compatible consolidation: signature preserved, one
optional parameter appended at the end (reported as CHANGED, but no caller breaks)."""
import time


class TransientError(Exception):
    pass


def retry(op, attempts=3, exc=TransientError, sleep=None, jitter=None):
    err = None
    for _ in range(attempts):
        try:
            return op()
        except exc as e:
            err = e
            if sleep:
                time.sleep(sleep + (jitter or 0))
    raise err

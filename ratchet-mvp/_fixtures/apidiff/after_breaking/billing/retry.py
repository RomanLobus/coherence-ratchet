"""Canonical retry helper after a careless consolidation: `attempts` renamed to `tries`,
the exception filter and sleep dropped — three contract breaks in one tidy-up."""


class TransientError(Exception):
    pass


def retry(op, tries=3):
    err = None
    for _ in range(tries):
        try:
            return op()
        except Exception as e:
            err = e
    raise err

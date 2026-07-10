from billing.retry import retry
from billing.paginate import paginate


def export_with_retry(fn, max_attempts=4):
    return retry(fn, attempts=max_attempts)


def chunk(rows, size=100):
    return paginate(rows, page_size=size)

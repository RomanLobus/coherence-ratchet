from billing.retry import retry


def submit_with_retry(op, tries=5):
    return retry(op, attempts=tries)

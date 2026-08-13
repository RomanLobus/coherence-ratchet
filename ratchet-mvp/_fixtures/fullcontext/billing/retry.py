"""Canonical retry helper. Transient-failure retries live here and only here."""
import time


def retry(operation, attempts: int = 3, delay: float = 0.5):
    """Call operation(), retrying up to `attempts` times on any exception, sleeping between tries."""
    last_error = None
    for _ in range(attempts):
        try:
            return operation()
        except Exception as error:
            last_error = error
            time.sleep(delay)
    raise last_error

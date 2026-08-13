import time


def retry(operation, attempts=3, delay=0.5):
    last_error = None
    for attempt in range(attempts):
        try:
            return operation()
        except Exception as error:
            last_error = error
            time.sleep(delay)
    raise last_error

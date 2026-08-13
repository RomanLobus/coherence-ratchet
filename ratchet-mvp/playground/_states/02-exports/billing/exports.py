import time


def export_with_retry(fn, max_attempts=4):
    captured = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as boom:
            captured = boom
            time.sleep(0.3)
    raise captured


def chunk(rows, size=100):
    out = []
    for offset in range(0, len(rows), size):
        out.append(rows[offset:offset + size])
    return out

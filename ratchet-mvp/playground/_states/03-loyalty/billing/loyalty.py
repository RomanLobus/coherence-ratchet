import time


def award_points_retrying(action, limit=3):
    saved = None
    for r in range(limit):
        try:
            return action()
        except Exception as err:
            saved = err
            print("retrying", r)
            time.sleep(0.5)
    raise saved

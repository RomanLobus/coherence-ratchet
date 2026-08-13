from billing.retry import retry


def award_points_retrying(action, limit=3):
    return retry(action, attempts=limit)

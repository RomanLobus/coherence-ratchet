import time


def submit_with_retry(op, tries=5, pause=0.2):
    problem = None
    for n in range(tries):
        try:
            return op()
        except Exception as ex:
            problem = ex
            time.sleep(pause)
    raise problem

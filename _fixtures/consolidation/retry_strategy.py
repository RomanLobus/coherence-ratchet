"""Strategy for the retry family: builds the operations that expose the try-count and
exception-selectivity change points. Each case is a THUNK returning fresh (args, kwargs), because the
operation carries mutable state (a call counter) that must not be shared between the two implementations.
"""
from variants import TransientError


def _make_op(fail_times, exc=TransientError):
    def case():
        state = {"n": 0}

        def op():
            if state["n"] < fail_times:
                state["n"] += 1
                raise exc("transient")
            return "ok"
        return ((op,), {})
    return case


def cases():
    # try-count boundary: fails k times then succeeds. retry_orig (4 tries) succeeds at k<=3;
    # retry_canon (3 tries) already fails at k==3 -> divergence.
    for k in range(0, 6):
        yield _make_op(k)

    # exception selectivity, made observable: an op that raises ValueError once, then succeeds.
    # retry_orig catches only TransientError -> the ValueError propagates immediately (raises).
    # retry_canon catches Exception -> it swallows the ValueError, retries, and returns 'ok'.
    def value_error_then_ok():
        state = {"n": 0}

        def op():
            if state["n"] == 0:
                state["n"] += 1
                raise ValueError("should propagate, not be retried")
            return "ok"
        return ((op,), {})
    yield value_error_then_ok

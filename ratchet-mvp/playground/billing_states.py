"""The playground decay, commit by commit.

A tiny billing subsystem starts coherent: one retry helper, one paginator.
Then an AI author adds features the way agents actually do — locally correct,
additive, each one quietly reimplementing something that already existed,
because nothing made it reuse the original. Redundancy climbs. Finally a
consolidation pass replaces the divergent copies with the canonical helpers
and the curve comes back down.

Each STEP is the full source tree at that point. `materialize()` writes a step
to a directory; the metric engine measures it. Nothing here is AI-generated at
run time — the decay is scripted so the demo is reproducible.
"""

from __future__ import annotations

import os

# --- the coherent baseline --------------------------------------------------

RETRY = '''\
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
'''

PAGINATE = '''\
def paginate(items, page_size=50):
    pages = []
    for start in range(0, len(items), page_size):
        pages.append(items[start:start + page_size])
    return pages
'''

MONEY = '''\
from decimal import Decimal


def to_cents(amount):
    return int((Decimal(str(amount)) * 100).to_integral_value())
'''

REFUNDS = '''\
from billing.retry import retry
from billing.money import to_cents


def issue_refund(gateway, order):
    return retry(lambda: gateway.refund(to_cents(order.amount)))
'''

BASELINE = {
    "billing/__init__.py": "",
    "billing/retry.py": RETRY,
    "billing/paginate.py": PAGINATE,
    "billing/money.py": MONEY,
    "billing/refunds.py": REFUNDS,
}

# --- the decay: each module reinvents retry / paginate instead of reusing ---

# orders.py: a near-copy of retry() with renamed locals and different numbers.
ORDERS_DIVERGENT = '''\
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
'''

# exports.py: yet another retry, plus a copy of paginate under a new name.
EXPORTS_DIVERGENT = '''\
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
'''

# loyalty.py: a third retry variant, this one with a stray log line.
LOYALTY_DIVERGENT = '''\
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
'''

# --- the consolidation: the same modules, now reusing the canonical helpers -

ORDERS_CONSOLIDATED = '''\
from billing.retry import retry


def submit_with_retry(op, tries=5):
    return retry(op, attempts=tries)
'''

EXPORTS_CONSOLIDATED = '''\
from billing.retry import retry
from billing.paginate import paginate


def export_with_retry(fn, max_attempts=4):
    return retry(fn, attempts=max_attempts)


def chunk(rows, size=100):
    return paginate(rows, page_size=size)
'''

LOYALTY_CONSOLIDATED = '''\
from billing.retry import retry


def award_points_retrying(action, limit=3):
    return retry(action, attempts=limit)
'''


def _step(base: dict, **overrides) -> dict:
    out = dict(base)
    out.update(overrides)
    return out


# Cumulative states. Each is the full tree at that commit.
_s0 = BASELINE
_s1 = _step(_s0, **{"billing/orders.py": ORDERS_DIVERGENT})
_s2 = _step(_s1, **{"billing/exports.py": EXPORTS_DIVERGENT})
_s3 = _step(_s2, **{"billing/loyalty.py": LOYALTY_DIVERGENT})
_s4 = _step(
    _s3,
    **{
        "billing/orders.py": ORDERS_CONSOLIDATED,
        "billing/exports.py": EXPORTS_CONSOLIDATED,
        "billing/loyalty.py": LOYALTY_CONSOLIDATED,
    },
)

STEPS = [
    ("00-baseline", "coherent: one retry, one paginator", _s0),
    ("01-orders", "orders.py reinvents retry", _s1),
    ("02-exports", "exports.py reinvents retry and paginate", _s2),
    ("03-loyalty", "loyalty.py reinvents retry a third time", _s3),
    ("04-consolidated", "divergent copies reuse the canonical helpers", _s4),
]


def materialize(files: dict, dest: str) -> str:
    for rel, src in files.items():
        path = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
    return dest

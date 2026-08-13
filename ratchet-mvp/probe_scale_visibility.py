"""Probe R3 — does lexical mismatch hide a helper once the package is large?

`scale-visibility-threshold.md` measured reuse collapsing with discoverability rather than size:
9/9 reuse when the canonical helper was lexically findable, even at 122 modules, and 6/6 reinvention
when the same helper in the same-size package was named in vocabulary the task did not share. Those
agents had grep and glob, and the mechanism was that a search for "cents" hit `money.py` or returned
nothing.

This harness has no tools, so that regime cannot be replicated faithfully and this probe does not
claim to. It runs the question the original leaves open for a toolless agent, which is the regime a
plain API call models and the one `fullcontext-fragmentation.md` already measured at small scale.
There, five modules in context with the helper renamed to jargon still produced 10/10 reuse: the model
read everything and matched on meaning rather than on name. The open question is whether that survives
a package twenty-five times larger, where reading everything stops being cheap.

Two conditions, identical but for the helper's name and vocabulary, both with the entire package in
context:

    match    the helper is `money.to_cents`, docstring speaks of cents, matching the task's wording
    jargon   the helper is `settle.to_minor_units`, docstring speaks of minor units and never of cents

The decoy modules are generated deterministically from a fixed seed, so the package is identical
across trials, conditions, vendors and re-runs. The canonical helper sits at the same index in both
conditions, so position is held constant and only the naming varies.

A trial reuses when the produced module imports or calls the canonical helper, and reinvents when it
builds its own conversion. Scored deterministically, no model in the loop.
"""

from __future__ import annotations

import os
import random
import re
import sys

N_MODULES = 122
HELPER_INDEX = 61  # middle of the package, held constant across conditions
SEED = 11

CONDITIONS = ("match", "jargon")

_TASK = (
    "Add a new module `shop/order_total.py` with a function `order_total(order)` that returns the "
    "order's total as an integer number of cents, summing `order['lines']` where each line has "
    "`qty` and `price` (price is a decimal amount in currency units, not cents). Return ONLY the "
    "full source of shop/order_total.py in one Python code block, no prose."
)

_HELPERS = {
    "match": (
        "money",
        '''"""Money helpers."""
from decimal import Decimal, ROUND_HALF_UP


def to_cents(amount):
    """Convert a decimal currency amount to an integer number of cents."""
    return int((Decimal(str(amount)) * 100).to_integral_value(rounding=ROUND_HALF_UP))
''',
    ),
    "jargon": (
        "settle",
        '''"""Settlement primitives."""
from decimal import Decimal, ROUND_HALF_UP


def to_minor_units(value):
    """Normalise a monetary value to its smallest indivisible denomination."""
    return int((Decimal(str(value)) * 100).to_integral_value(rounding=ROUND_HALF_UP))
''',
    ),
}

_DOMAINS = [
    ("catalogue", "product listings"), ("basket", "in-progress baskets"),
    ("fulfilment", "warehouse dispatch"), ("returns", "return authorisations"),
    ("loyalty", "points balances"), ("promos", "promotional rules"),
    ("stock", "inventory counts"), ("supplier", "supplier records"),
    ("courier", "courier bookings"), ("address", "address validation"),
    ("session", "customer sessions"), ("audit", "audit trail entries"),
    ("search", "search indexing"), ("reviews", "product reviews"),
    ("wishlist", "saved items"), ("gifting", "gift messages"),
    ("subscriptions", "recurring orders"), ("regions", "regional settings"),
    ("locale", "language selection"), ("consent", "consent records"),
]


def _decoys(n: int) -> list[tuple[str, str]]:
    """Deterministic filler modules: plausible, unrelated, and none about currency conversion."""
    rng = random.Random(SEED)
    out = []
    for i in range(n):
        base, what = _DOMAINS[i % len(_DOMAINS)]
        name = f"{base}_{i // len(_DOMAINS)}" if i >= len(_DOMAINS) else base
        verb = rng.choice(["load", "list", "resolve", "summarise", "validate", "index"])
        arg = rng.choice(["record", "entry", "row", "item", "request"])
        src = (
            f'"""{what.capitalize()}."""\n\n\n'
            f"def {verb}_{base}({arg}, options=None):\n"
            f'    """{verb.capitalize()} {what} for the given {arg}."""\n'
            f"    options = options or {{}}\n"
            f"    return {{'{base}': {arg}, 'options': options}}\n"
        )
        out.append((name, src))
    return out


def _package(condition: str) -> str:
    helper_mod, helper_src = _HELPERS[condition]
    mods = _decoys(N_MODULES - 1)
    mods.insert(HELPER_INDEX, (helper_mod, helper_src))
    return "\n\n".join(f"# ===== shop/{name}.py =====\n{src}" for name, src in mods)


def build_prompt(condition: str) -> str:
    if condition not in _HELPERS:
        raise ValueError(condition)
    return (
        "You are adding a module to this Python package. Its full current source is below.\n\n"
        + _package(condition) + "\n\n" + _TASK
    )


# --- deterministic scorer ---------------------------------------------------

def score_code(code: str, *_names) -> dict:
    """Reuse of either canonical helper, against a conversion written from scratch."""
    reuse_match = bool(re.search(r"(?<![\w])to_cents\s*\(", code)) or "import to_cents" in code
    reuse_jargon = bool(re.search(r"(?<![\w])to_minor_units\s*\(", code)) or "import to_minor_units" in code
    # Its own conversion: a hundred-multiplication or a Decimal quantise inside the produced module.
    own = bool(re.search(r"\*\s*100|100\s*\*|quantize|to_integral_value|round\s*\(", code))
    reuse = reuse_match or reuse_jargon
    return {
        "reuse": reuse,
        "reuse_match_name": reuse_match,
        "reuse_jargon_name": reuse_jargon,
        "reinvented": own and not reuse,
        "imports_helper_module": bool(re.search(r"from\s+\.?(?:shop\.)?(money|settle)\s+import", code)),
    }


def tally(results_dir: str) -> None:
    print(f"{'condition':<10} {'n':>3}  reuse  reinvented")
    for cond in CONDITIONS:
        d = os.path.join(results_dir, cond)
        if not os.path.isdir(d):
            continue
        rows = []
        for name in sorted(os.listdir(d)):
            if name.endswith(".extracted.py"):
                with open(os.path.join(d, name), encoding="utf-8") as f:
                    rows.append(score_code(f.read()))
        if rows:
            print(f"{cond:<10} {len(rows):>3}  {sum(r['reuse'] for r in rows):>5}  "
                  f"{sum(r['reinvented'] for r in rows):>10}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--print":
        print(build_prompt(sys.argv[2]))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--tally":
        tally(sys.argv[2])
    else:
        print(__doc__)

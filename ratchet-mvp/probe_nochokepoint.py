"""Probe N2: the cross-cutting change with no chokepoint to route through.

`reframe-A-self-model.md` measured a derived self-model taking cross-cutting consistency from 1/8 to
8/8, and named its own weakness in the caveats: the fixture kept a `create` function that materialised
both order shapes, so the blind arm *could* succeed by routing through it, and one trial in eight did.
Chapter 12 concedes the truly independent case is argued from that boundary and not directly measured.
That undemonstrated case is the regime the book's claim actually describes, so it is the one worth
measuring.

This fixture removes the chokepoint. An order total is computed at two sites that share no ancestor,
no caller, and no materialising function:

    shop/billing.py    invoice_total(order)       sums order["lines"]  as qty * price
    shop/analytics.py  revenue_for_order(order)   sums order["items"]  as count * cents

No module reads both keys. `shipping.py` also reads `order["lines"]`, which makes the tree realistic
without creating a path between the two totals, and `customers.py` reads neither. Both functions
return 1300 on the fixture order, so a correct change leaves both returning 1170 and the oracle is one
number rather than a judgement.

Two arms:

  blind      the agent sees billing, shipping and customers. The analytics site is not in context.
  selfmodel  the same, plus a derived self-model naming every site that computes an order total, and
             the analytics source the model pointed at.

The second arm bundles naming a site with granting access to it, which is faithful to how a query
works and is the same bundling the original run disclosed. A purist split remains untested.

The oracle executes the returned modules against the fixture order. A trial is consistent only when
both sites return the discounted total; patching billing alone is the divergence bug the probe exists
to count.
"""

from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "_fixtures", "nochokepoint", "shop")

ORDER = {
    "id": 7,
    "region": "eu",
    "lines": [{"qty": 2, "price": 400}, {"qty": 1, "price": 500}],
    "items": [{"count": 2, "cents": 400}, {"count": 1, "cents": 500}],
}
UNDISCOUNTED = 1300
DISCOUNTED = 1170

TASK = (
    "Apply a 10 percent discount to the order total, everywhere the order total is computed, "
    "consistently. Return the FULL source of every file you change, each in its own Python code "
    "block preceded by a line of the form `# ===== shop/<name>.py =====`. Change nothing else."
)

SELFMODEL = (
    "The derived self-model for this package reports that the order total is computed at TWO sites:\n"
    "  - `shop.billing.invoice_total(order)`    over `order['lines']` as qty * price\n"
    "  - `shop.analytics.revenue_for_order(order)` over `order['items']` as count * cents\n"
    "The two sites use different field shapes for the same quantity.\n"
)


def _read(name: str) -> str:
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return f.read()


def _source(names) -> str:
    return "\n\n".join(f"# ===== shop/{n} =====\n{_read(n)}" for n in names)


BLIND_FILES = ("billing.py", "shipping.py", "customers.py")
ALL_FILES = ("billing.py", "shipping.py", "customers.py", "analytics.py")

CONDITIONS = ("blind", "selfmodel")


def build_prompt(condition: str) -> str:
    if condition == "blind":
        return ("You are making a change to this Python package. Its source is below.\n\n"
                + _source(BLIND_FILES) + "\n\n" + TASK)
    if condition == "selfmodel":
        return ("You are making a change to this Python package. Its source is below.\n\n"
                + _source(ALL_FILES) + "\n\n" + SELFMODEL + "\n" + TASK)
    raise ValueError(condition)


# --- deterministic oracle ---------------------------------------------------

_HEADER = re.compile(r"#\s*=====\s*shop/(\w+)\.py\s*=====")


def _modules_from(text: str) -> dict[str, str]:
    """Split a response into {module: source} on the headers the task asked for.

    Falls back to attributing a single unheadered block to whichever target function it defines, so a
    response that ignored the header convention is still scored on what it did rather than discarded.
    """
    blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", text, re.S) or [text]
    out: dict[str, str] = {}
    for block in blocks:
        parts = _HEADER.split(block)
        if len(parts) > 1:
            for name, body in zip(parts[1::2], parts[2::2]):
                out[name] = out.get(name, "") + body
        elif "def invoice_total" in block:
            out["billing"] = out.get("billing", "") + block
        elif "def revenue_for_order" in block:
            out["analytics"] = out.get("analytics", "") + block
    return out


def _call(source: str, func: str):
    """Execute one produced module in a fresh namespace and call the target function."""
    ns: dict = {}
    try:
        exec(compile(source, "<produced>", "exec"), ns)  # noqa: S102 - probe oracle, local fixture
    except Exception:
        return None
    fn = ns.get(func)
    if not callable(fn):
        return None
    try:
        return fn(dict(ORDER))
    except Exception:
        return None


def score_code(text: str, *_names) -> dict:
    """Did the change reach both sites? Executed, not inspected."""
    mods = _modules_from(text)

    billing_src = mods.get("billing")
    analytics_src = mods.get("analytics")

    billing_val = _call(billing_src, "invoice_total") if billing_src else None
    analytics_val = _call(analytics_src, "revenue_for_order") if analytics_src else None

    # A site the response did not return is unchanged, so it still computes the undiscounted total.
    billing_effective = billing_val if billing_val is not None else UNDISCOUNTED
    analytics_effective = analytics_val if analytics_val is not None else UNDISCOUNTED

    billing_ok = billing_effective == DISCOUNTED
    analytics_ok = analytics_effective == DISCOUNTED

    return {
        "billing_discounted": billing_ok,
        "analytics_discounted": analytics_ok,
        "consistent": billing_ok and analytics_ok,
        "divergence_bug": billing_ok and not analytics_ok,
        "touched_analytics": analytics_src is not None,
        "billing_value": billing_effective,
        "analytics_value": analytics_effective,
    }


def tally(results_dir: str) -> None:
    print(f"{'arm':<12} {'n':>3}  consistent  divergence-bug  touched-analytics")
    for cond in CONDITIONS:
        d = os.path.join(results_dir, cond)
        if not os.path.isdir(d):
            continue
        rows = []
        for name in sorted(os.listdir(d)):
            if name.endswith(".extracted.py"):
                with open(os.path.join(d, name), encoding="utf-8") as f:
                    rows.append(score_code(f.read()))
        if not rows:
            continue
        c = sum(r["consistent"] for r in rows)
        b = sum(r["divergence_bug"] for r in rows)
        t = sum(r["touched_analytics"] for r in rows)
        print(f"{cond:<12} {len(rows):>3}  {c:>10}  {b:>14}  {t:>17}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--print":
        print(build_prompt(sys.argv[2]))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--tally":
        tally(sys.argv[2])
    else:
        print(__doc__)

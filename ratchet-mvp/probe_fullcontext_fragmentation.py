"""Probe: does more context fix fragmentation, or does surfacing?

Threat to the book: "AI will fix this itself — bigger context windows and better models will just reuse
what's already there." This probe tests that directly. A subsystem already contains two clearly-named
canonical helpers (`billing.money.to_cents`, `billing.retry.retry`). An agent is asked to write a new
function that needs both, under three conditions:

  (a) task-only        — only the task and the target file (the helper is not visible at all: the floor)
  (b) full-context     — the ENTIRE subsystem source in context (the helper is right there to discover)
  (c) full+surfaced    — full context PLUS the self-model pointing at the canonical helpers (the method's
                          lever: prevention by visibility)

The question is (b) vs (c): if merely having the whole codebase in context does NOT make the agent
reuse the helper, then a larger window is not the fix — surfacing is. That is the empirical answer to
"AI will fix it".

This file holds the fixture-embedding prompt builders and a DETERMINISTIC scorer (reuse vs reinvention
detected from the produced code). Trials are run by spawning coding subagents with the built prompts;
each returned `charges.py` is saved under a results dir and tallied here.

    python3 probe_fullcontext_fragmentation.py --print {task_only|full_context|full_surfaced}
    python3 probe_fullcontext_fragmentation.py --tally <results_dir>   # subdirs: task_only/ full_context/ full_surfaced/
"""
from __future__ import annotations

import ast
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "_fixtures", "fullcontext")

TASK = (
    "Implement a new module `billing/charges.py` with a function "
    "`charge_customer(order, gateway)` that converts the order's amount (`order['amount']`) to integer "
    "cents and submits the charge via `gateway.submit(order['id'], amount_cents)`, retrying on transient "
    "failure. Return ONLY the full source of billing/charges.py in one Python code block, no prose."
)

SELFMODEL_SURFACED = (
    "This subsystem's derived self-model records these CANONICAL helpers you should reuse:\n"
    "  - currency->cents conversion: `billing.money.to_cents(amount)`\n"
    "  - transient-failure retry:    `billing.retry.retry(operation, attempts, delay)`\n"
    "Reuse them; do not reimplement conversion or retry.\n"
)


# A grounding block in the same form, register and imperative mood as SELFMODEL_SURFACED, naming
# helpers that do not exist. The subsystem source is in context either way, so the real `to_cents`
# and `retry` are plainly visible while this text asserts a different canon.
#
# This is the control the grounding results needed. Every earlier arm compared no grounding against
# correct grounding, which cannot separate "the grounding named the right thing" from "an
# authoritative-sounding block changes behaviour". If an agent follows this block over the code in
# front of it, then a derived model nobody ratified does not merely fail to help: it actively
# misleads, which is the claim Chapter 4 opens on.
SELFMODEL_SHAM = (
    "This subsystem's derived self-model records these CANONICAL helpers you should reuse:\n"
    "  - currency->cents conversion: `billing.money.to_minor_units(amount)`\n"
    "  - transient-failure retry:    `billing.resilience.with_backoff(operation, attempts, delay)`\n"
    "Reuse them; do not reimplement conversion or retry.\n"
)

# The names the sham block asserts. Neither exists anywhere in the fixture.
SHAM_NAMES = ("to_minor_units", "with_backoff")


def _read(rel):
    with open(os.path.join(FIX, rel), encoding="utf-8") as f:
        return f.read()


def _subsystem_source():
    parts = []
    for rel in ("billing/money.py", "billing/retry.py", "billing/orders.py", "billing/paginate.py"):
        parts.append(f"# ===== {rel} =====\n{_read(rel)}")
    return "\n\n".join(parts)


# Condition (d): the SAME two canonical helpers exist and are in full context, but named in opaque
# jargon with docstrings that never say "cents" or "retry", among unrelated noise modules. This tests
# whether presence-in-context alone drives reuse, or whether discoverability (a matchable name) does —
# the small-scale analogue of P7 (a jargon-named helper reinvented at 122 modules).
_BURIED_SOURCE = '''# ===== billing/internal/num.py =====
"""Numeric normalisation utilities."""
from decimal import Decimal, ROUND_HALF_UP


def _q(v):
    """Normalise a value to its minor-unit integer representation."""
    return int((Decimal(str(v)) * 100).to_integral_value(rounding=ROUND_HALF_UP))


# ===== billing/internal/exec.py =====
"""Execution helpers."""
import time


def _attempt(fn, n=3, pause=0.5):
    """Run fn a few times, tolerating hiccups."""
    err = None
    for _ in range(n):
        try:
            return fn()
        except Exception as e:
            err = e
            time.sleep(pause)
    raise err


# ===== billing/reports.py =====
"""Reporting."""
def monthly_totals(rows):
    return sum(r["value"] for r in rows)


# ===== billing/customers.py =====
"""Customer records."""
def display_name(customer):
    return f"{customer['first']} {customer['last']}"


# ===== billing/tax.py =====
"""Tax."""
def apply_rate(base, rate):
    return base + base * rate
'''


EXHORTATION = (
    "Engineering standard for this repository:\n"
    "Reuse the package's existing helpers wherever one already does what you need. If you write a\n"
    "new function that duplicates something already present, you must justify the duplication in a\n"
    "comment above it explaining why the existing helper could not be used.\n"
)

def build_prompt(condition: str) -> str:
    if condition == "task_only":
        return (
            "You are adding a function to a Python billing package. You are writing the file "
            "`billing/charges.py`.\n\n" + TASK
        )
    if condition == "full_context":
        return (
            "You are adding a function to this Python billing package. Its full current source is below.\n\n"
            + _subsystem_source() + "\n\n" + TASK
        )
    if condition == "full_surfaced":
        return (
            "You are adding a function to this Python billing package. Its full current source is below.\n\n"
            + _subsystem_source() + "\n\n" + SELFMODEL_SURFACED + "\n" + TASK
        )
    if condition == "full_exhort":
        # The exhortation arm. Same visible source as full_context, plus an instruction to reuse or
        # justify. Nothing is surfaced: the agent is told to be diligent, not told what exists. This
        # is the arm that isolates willingness from visibility, which is the whole question.
        return (
            "You are adding a function to this Python billing package. Its full current source is below.\n\n"
            + _subsystem_source() + "\n\n" + EXHORTATION + "\n" + TASK
        )
    if condition == "task_sham":
        # The regime where grounding is load-bearing: the agent cannot see the subsystem, so the
        # block is its only account of what exists. If it follows a canon that is not there, an
        # unratified model has not merely failed to help; it has caused the defect.
        return (
            "You are adding a function to a Python billing package. You are writing the file "
            "`billing/charges.py`.\n\n" + SELFMODEL_SHAM + "\n" + TASK
        )
    if condition == "full_sham":
        return (
            "You are adding a function to this Python billing package. Its full current source is below.\n\n"
            + _subsystem_source() + "\n\n" + SELFMODEL_SHAM + "\n" + TASK
        )
    if condition == "full_buried":
        return (
            "You are adding a function to this Python billing package. Its full current source is below.\n\n"
            + _BURIED_SOURCE + "\n\n" + TASK
        )
    raise ValueError(condition)


# --- deterministic scorer ---------------------------------------------------

import re


def score_code(code: str, cents_name: str = "to_cents", retry_name: str = "retry") -> dict:
    """Detect reuse vs reinvention of each canonical helper from produced code.

    Reuse = imports the canonical helper or calls its name at a word boundary (kept distinct from a
    reinvented `_to_cents(` or a locally-defined `def retry`). Reinvention = an own conversion / own
    retry loop. The canonical names are parameters so the buried condition (jargon `_q`/`_attempt`)
    scores the same way.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        tree = None

    calls_canonical_cents = bool(re.search(r"(?<![\w])" + re.escape(cents_name) + r"\s*\(", code))
    calls_canonical_retry = (bool(re.search(r"(?<![\w])" + re.escape(retry_name) + r"\s*\(", code))
                             and f"def {retry_name}" not in code)
    reuse_cents = "billing.money" in code or "import to_cents" in code or calls_canonical_cents
    reuse_retry = "billing.retry" in code or "import retry" in code or calls_canonical_retry

    # reinvention: an own conversion (Decimal/*100/quantize/round) or an own attempt loop, when the
    # canonical helper was NOT reused.
    own_conversion = bool(re.search(r"Decimal|\*\s*100|quantize|round\s*\(", code))
    reinvent_cents = own_conversion and not calls_canonical_cents

    reinvent_retry = False
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name != "retry":
                has_loop = any(isinstance(n, (ast.For, ast.While)) for n in ast.walk(node))
                has_try = any(isinstance(n, ast.Try) for n in ast.walk(node))
                if has_loop and has_try and not calls_canonical_retry:
                    reinvent_retry = True
    return {
        "reuse_cents": bool(reuse_cents and not reinvent_cents),
        "reuse_retry": bool(reuse_retry and not reinvent_retry),
        "reinvent_cents": bool(reinvent_cents),
        "reinvent_retry": bool(reinvent_retry),
    }


# canonical helper names per condition (buried uses the jargon names)
_NAMES = {
    "task_only": ("to_cents", "retry"),
    "full_context": ("to_cents", "retry"),
    "full_surfaced": ("to_cents", "retry"),
    "task_sham": ("to_cents", "retry"),
    "full_sham": ("to_cents", "retry"),
    "full_buried": ("_q", "_attempt"),
}

# The dispatcher's contract, so `experiments/harness` can run this probe without knowing anything
# about it: the conditions to sweep, and the canonical names its scorer needs per condition. Both
# were already here under private names; exposing them is what makes the run re-runnable rather than
# recorded, and changes no behaviour.
CONDITIONS = ("task_only", "task_sham", "full_context", "full_exhort", "full_surfaced",
              "full_sham", "full_buried")
CANONICAL_NAMES = _NAMES


def tally(results_dir: str):
    """Score one run directory, one row per condition actually present.

    Two defects lived here. The condition list was a hard-coded subset, so an arm added to the probe
    was silently absent from its own results; and the file glob matched every `.py` a trial writes,
    counting each trial two or three times and reporting an n that was a multiple of the trials
    actually run. Both produced a plausible table, which is what made them worth a test.
    """
    present = sorted(d for d in os.listdir(results_dir)
                     if os.path.isdir(os.path.join(results_dir, d)))
    unknown = [d for d in present if d not in CONDITIONS]
    print(f"{'condition':<16} {'n':>3}  reuse_cents  reuse_retry  reinvent_cents  reinvent_retry")
    for cond in [c for c in CONDITIONS if c in present] + unknown:
        d = os.path.join(results_dir, cond)
        # One file per trial. `trial-NN.round0.py` and `trial-NN.raw.json` are the same trial.
        files = [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith(".extracted.py")]
        if not files:
            print(f"{cond:<16} {0:>3}  no extracted code; the trials failed or wrote nothing")
            continue
        cents_name, retry_name = _NAMES.get(cond, ("to_cents", "retry"))
        agg = {"reuse_cents": 0, "reuse_retry": 0, "reinvent_cents": 0, "reinvent_retry": 0}
        for path in files:
            sc = score_code(open(path, encoding="utf-8").read(), cents_name, retry_name)
            for k in agg:
                agg[k] += int(sc[k])
        n = len(files)
        print(f"{cond:<16} {n:>3}  {agg['reuse_cents']:>10}/{n} "
              f"{agg['reuse_retry']:>10}/{n} {agg['reinvent_cents']:>12}/{n} "
              f"{agg['reinvent_retry']:>12}/{n}")
    if unknown:
        print(f"\nnote: {', '.join(unknown)} present in the run and not declared in CONDITIONS")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--print":
        print(build_prompt(sys.argv[2]))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--tally":
        tally(sys.argv[2])
    else:
        print(__doc__)

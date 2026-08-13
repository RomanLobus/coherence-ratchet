"""Probe — author, detect, revise: the loop, with a committed harness.

`feedback-loop.md` is the programme's strongest result. An agent given a task but not the file holding
the canonical helper reinvented the conversion in all ten trials; a detector that could see the
codebase named the collision in all ten; handed the finding, the agent reused the canonical helper in
all ten. Zero out of ten to ten out of ten, with nothing surfaced in advance.

It was a recorded run. The prompts and the returned code lived in a session scratchpad, and the
detector was an agent someone spawned by hand, so nobody else could re-run it. This probe commits all
three stages.

The detector matters, and `advise-detector-boundary.md` settles which one may be used. The shipped
deterministic detector named a collision in **none** of ten real reinventions, because a freshly
written `Decimal.quantize` conversion and the canonical `to_integral_value` helper share almost no
structure. The loop therefore closes only with a detector that reasons about meaning, and this probe
uses a model for that step, which is what the original did. Presenting the deterministic command as
the mechanism behind this number would be a claim the measurement contradicts.

One departure from the original is worth stating plainly. The original fed the finding back into the
same live session. This harness has no session, so round two is a single prompt carrying the original
task, the code the agent produced, and the detector's finding. That is a reconstruction of the loop
rather than the loop itself, and an agent with true conversational memory might behave differently.

    round 1   the agent writes `billing/charges.py` with the canonical helpers out of context
    detect    a separate call sees the subsystem and the produced code, and names any duplication
    round 2   the finding is handed back and the agent revises

Both rounds are scored by the same deterministic scorer, so the result is a before and an after.
"""

from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIX = os.path.join(HERE, "_fixtures", "fullcontext")

CONDITIONS = ("loop",)

_TASK = (
    "Implement a new module `billing/charges.py` with a function "
    "`charge_customer(order, gateway)` that converts the order's amount (`order['amount']`) to integer "
    "cents and submits the charge via `gateway.submit(order['id'], amount_cents)`, retrying on transient "
    "failure. Return ONLY the full source of billing/charges.py in one Python code block, no prose."
)


def _read(rel: str) -> str:
    with open(os.path.join(FIX, rel), encoding="utf-8") as f:
        return f.read()


def _subsystem() -> str:
    return "\n\n".join(
        f"# ===== {rel} =====\n{_read(rel)}"
        for rel in ("billing/money.py", "billing/retry.py", "billing/orders.py", "billing/paginate.py")
    )


def build_prompt(condition: str = "loop") -> str:
    """Round one: the agent cannot see the helpers it needs, which is the ordinary condition."""
    return ("You are adding a function to a Python billing package. You are writing the file "
            "`billing/charges.py`.\n\n" + _TASK)


_DETECT = (
    "You are reviewing a change to a Python billing package. The package's existing source is below, "
    "followed by a new module a colleague has just written.\n\n"
    "{subsystem}\n\n"
    "# ===== the new module =====\n{code}\n\n"
    "Does the new module reimplement something the package already provides? Answer with one line per "
    "collision, in the form `DUPLICATES <existing.qualified.name>: <what it reimplements>`. If it "
    "duplicates nothing, answer exactly NONE."
)

_REVISE = (
    "You are adding a function to a Python billing package. You are writing the file "
    "`billing/charges.py`.\n\n{task}\n\n"
    "You produced this:\n\n```python\n{code}\n```\n\n"
    "A reviewer with sight of the whole package reports:\n\n{finding}\n\n"
    "Revise `billing/charges.py` accordingly. Return ONLY the full source in one Python code block, "
    "no prose."
)


def followup(first_response: str, ask) -> str | None:
    """Detect against the real codebase, then hand the finding back. None when nothing was found."""
    code = _extract(first_response)
    if not code.strip():
        return None
    finding = ask(_DETECT.format(subsystem=_subsystem(), code=code)).strip()
    if not finding or finding.upper().startswith("NONE"):
        return None
    return _REVISE.format(task=_TASK, code=code, finding=finding)


_FENCE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.S)


def _extract(text: str) -> str:
    blocks = _FENCE.findall(text or "")
    return "\n".join(blocks) if blocks else (text or "")


# --- deterministic scorer ---------------------------------------------------

def score_code(code: str, cents_name: str = "to_cents", retry_name: str = "retry") -> dict:
    reuse_cents = bool(re.search(r"(?<![\w])" + cents_name + r"\s*\(", code)) or \
        bool(re.search(r"import[^\n]*\b" + cents_name + r"\b", code))
    reuse_retry = (bool(re.search(r"(?<![\w])" + retry_name + r"\s*\(", code)) or
                   bool(re.search(r"import[^\n]*\b" + retry_name + r"\b", code))) and \
        f"def {retry_name}" not in code
    own_cents = bool(re.search(r"Decimal|quantize|to_integral_value|\*\s*100", code)) and not reuse_cents
    return {
        "reuse_cents": reuse_cents,
        "reuse_retry": reuse_retry,
        "reuse_both": reuse_cents and reuse_retry,
        "reinvent_cents": own_cents,
    }


def tally(results_dir: str) -> None:
    d = os.path.join(results_dir, "loop")
    if not os.path.isdir(d):
        return
    before = after = detected = n = 0
    for name in sorted(os.listdir(d)):
        if not name.endswith(".round0.py"):
            continue
        n += 1
        stem = name[: -len(".round0.py")]
        with open(os.path.join(d, name), encoding="utf-8") as f:
            r0 = score_code(f.read())
        final_path = os.path.join(d, stem + ".extracted.py")
        with open(final_path, encoding="utf-8") as f:
            r1 = score_code(f.read())
        before += r0["reuse_both"]
        after += r1["reuse_both"]
        detected += os.path.exists(os.path.join(d, stem + ".followup.raw.json"))
    print(f"  trials ................. {n}")
    print(f"  reuse before feedback .. {before}/{n}")
    print(f"  detector fired ......... {detected}/{n}")
    print(f"  reuse after feedback ... {after}/{n}")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--print":
        print(build_prompt())
    elif len(sys.argv) >= 3 and sys.argv[1] == "--tally":
        tally(sys.argv[2])
    else:
        print(__doc__)

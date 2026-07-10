"""Replay the billing decay through the coherence ratchet.

Run from the ratchet-mvp directory:

    python demo.py

It materialises each commit into playground/_states/<label>/ (inspectable and
diffable), measures coherence, prints the rising-then-falling redundancy curve,
and shows the ratchet tripping on the decay commits and holding on the
consolidation.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "playground"))

import billing_states as bs  # noqa: E402
from coherence_ratchet import measure  # noqa: E402
from coherence_ratchet.ratchet import Budget, append_ledger  # noqa: E402


def bar(value: float, scale: float, width: int = 32) -> str:
    n = 0 if scale <= 0 else round(value / scale * width)
    return "#" * n


def main() -> int:
    states_dir = os.path.join(HERE, "playground", "_states")
    snapshots = []
    for label, note, files in bs.STEPS:
        dest = os.path.join(states_dir, label)
        bs.materialize(files, dest)
        snapshots.append((label, note, measure(dest)))

    max_clusters = max(s.redundant_clusters for _, _, s in snapshots) or 1
    max_ratio = max(s.duplication_ratio for _, _, s in snapshots) or 1.0

    print("\nCoherence curve — redundant clusters (the decay signal)\n")
    print(f"  {'commit':<18}{'clusters':>9}  {'dup-ratio':>9}   chart")
    for label, note, s in snapshots:
        print(
            f"  {label:<18}{s.redundant_clusters:>9}  {s.duplication_ratio:>9.2f}   "
            f"{bar(s.redundant_clusters, max_clusters)}"
        )
    print("\n  (each '#' is a near-duplicate cluster — the same idea built again)\n")

    # The ratchet: baseline sets the budget; later commits are checked against it.
    baseline_snap = snapshots[0][2]
    budget = Budget.from_snapshot(baseline_snap)
    ledger = os.path.join(states_dir, "coherence-ledger.jsonl")
    if os.path.exists(ledger):
        os.remove(ledger)

    print("Ratchet decisions (budget fixed at the baseline):\n")
    for i, (label, note, s) in enumerate(snapshots):
        breaches = budget.breaches(s)
        if breaches:
            worst = ", ".join(f"{b.metric} {b.observed}>{b.ceiling}" for b in breaches)
            print(f"  {label:<18} TRIPPED  ({worst})")
            if label == "01-orders":
                append_ledger(
                    ledger,
                    when="2026-06-25",
                    region="billing",
                    breaches=breaches,
                    owner="billing-steward",
                    repayment_trigger="before next orders change",
                    note=note,
                )
                print(f"  {'':<18}          -> debt accepted, ledger entry written")
        else:
            print(f"  {label:<18} OK       (coherence held)")

    print(f"\nLedger: {os.path.relpath(ledger, HERE)}")
    print("Inspect the states: playground/_states/<commit>/billing/\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

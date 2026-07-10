"""The ratchet itself: a budget that can only hold or tighten, plus the
coherence-debt ledger that records every breach somebody chose to accept.

All watched metrics are "lower is better" (fewer redundant clusters, less
duplication, looser coupling is worse). The ratchet rule is therefore: a new
measurement may be less than or equal to the ceiling, never greater. When it
improves, the ceiling drops to meet it, so the gain cannot be given back.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from .metrics import Snapshot, measure

# The metric PORTFOLIO the ratchet watches. All are unambiguously lower-is-better.
# No single metric is enough (a red-team passed a fragmenting change past any one of them,
# P4/P8), so the ratchet watches a portfolio. Coupling (total_internal_edges,
# max_module_fanout, coupling_density) and hyperliminal/contagion are measured and reported
# as DIAGNOSTICS but deliberately NOT ratcheted: consolidating duplicates raises healthy
# coupling to the shared helper, so ratcheting it would punish the very fix the ratchet
# rewards. The deterministic portfolio is a floor, not a game-proof gate — the LLM semantic
# pass and the behaviour-complete proof (out of this module) are the load-bearing layers above.
#
# A Budget watches only the WATCHED keys that are PRESENT in the snapshot it is built from, so a
# function-level Snapshot ratchets the duplication subset and a Composite ratchets the full
# portfolio (cycles + duplication + connascence) — backward-compatible either way.
WATCHED = (
    "redundant_clusters",
    "redundant_functions",
    "duplication_ratio",
    "cycle_ratio",           # headline architectural signal (Composite only)
    "connascence_shared",    # implicit shared agreements (Composite only)
)


@dataclass
class Breach:
    metric: str
    ceiling: float
    observed: float

    @property
    def delta(self) -> float:
        return round(self.observed - self.ceiling, 4)


@dataclass
class Budget:
    ceilings: dict[str, float]

    @classmethod
    def from_snapshot(cls, snap) -> "Budget":
        # Accepts a function-level Snapshot or a composite (anything with .to_dict()).
        # Watches only the WATCHED metrics actually present, so the same ratchet handles the
        # duplication-only Snapshot and the full portfolio without code changes.
        d = snap.to_dict()
        return cls(ceilings={m: d[m] for m in WATCHED if m in d})

    @classmethod
    def load(cls, path: str) -> "Budget":
        with open(path, encoding="utf-8") as f:
            return cls(ceilings=json.load(f)["ceilings"])

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"ceilings": self.ceilings}, f, indent=2, sort_keys=True)
            f.write("\n")

    def breaches(self, snap) -> list[Breach]:
        d = snap.to_dict()
        out = []
        for m in self.ceilings:
            if m in d and d[m] > self.ceilings[m]:
                out.append(Breach(metric=m, ceiling=self.ceilings[m], observed=d[m]))
        return out

    def improvements(self, snap) -> dict[str, tuple[float, float]]:
        d = snap.to_dict()
        return {
            m: (self.ceilings[m], d[m]) for m in self.ceilings if m in d and d[m] < self.ceilings[m]
        }


def init_budget(root: str, budgets_path: str, repo: str | None = None) -> Budget:
    from .signals import measure_all

    budget = Budget.from_snapshot(measure_all(root, repo=repo))
    budget.save(budgets_path)
    return budget


def tighten(budget: Budget, snap) -> Budget:
    """Ratchet the ceilings down to meet an improved measurement."""
    d = snap.to_dict()
    new = {m: (min(v, d[m]) if m in d else v) for m, v in budget.ceilings.items()}
    return Budget(ceilings=new)


def check(root: str, budgets_path: str, repo: str | None = None):
    """Measure the portfolio and compare against saved ceilings.
    Uses the composite signal set (measure_all) so a portfolio budget ratchets the full set;
    a duplication-only budget still works via present-key filtering."""
    from .signals import measure_all

    budget = Budget.load(budgets_path)
    snap = measure_all(root, repo=repo)
    return snap, budget.breaches(snap), budget.improvements(snap)


def append_ledger(
    ledger_path: str,
    *,
    when: str,
    region: str,
    breaches: list[Breach],
    owner: str,
    repayment_trigger: str,
    note: str = "",
) -> None:
    """Append-only coherence-debt entry (JSON Lines)."""
    os.makedirs(os.path.dirname(ledger_path) or ".", exist_ok=True)
    entry = {
        "when": when,
        "region": region,
        "owner": owner,
        "repayment_trigger": repayment_trigger,
        "note": note,
        "breaches": [
            {"metric": b.metric, "ceiling": b.ceiling, "observed": b.observed}
            for b in breaches
        ],
    }
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")

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
from dataclasses import dataclass, field

from .metrics import Snapshot, measure

# The metric PORTFOLIO the ratchet watches. All are unambiguously lower-is-better.
# No single metric is enough (a red-team passed a fragmenting change past any one of them,
# P4/P8), so the ratchet watches a portfolio. Coupling (total_internal_edges,
# max_module_fanout, coupling_density) and hyperliminal/contagion are measured and reported
# as DIAGNOSTICS but deliberately NOT ratcheted: consolidating duplicates raises healthy
# coupling to the shared helper, so ratcheting it would punish the very fix the ratchet
# rewards. The deterministic portfolio is a floor, not an architectural decision: semantic
# candidate surfacing, compatibility evidence, bounded comparison, and review remain separate.
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

# Denominator decomposition for every ratio the portfolio reports. A ratio alone misleads under
# volume inflation: Larsen & Moghaddam (SEAA 2026) found agentic-AI adoption left smell counts
# unchanged (+1.1%, p=.82) while LOC grew +12.8%, so every density metric "improved" while the
# raw decay stayed put. Raw counts and explicit decomposition are therefore reported beside each
# ratio, everywhere it appears (measure/check output, breach messages, ledger entries).
# metric -> (numerator_key, denominator_key, numerator_label, denominator_label)
DECOMPOSITIONS = {
    "duplication_ratio": ("redundant_functions", "total_functions", "redundant", "functions"),
    "cycle_ratio": ("cyclic_modules", "n_modules", "cyclic", "modules"),
    "coupling_density": ("n_edges", "n_modules", "edges", "modules"),
    "max_fan_in_ratio": ("max_fan_in", "n_modules", "max fan-in", "modules"),
}

EXPOSURE_DIMENSIONS = (
    "volatility",
    "coordination_span",
    "criticality",
    "discoverability",
    "blast_radius",
)
EXPOSURE_LEVELS = {"low", "medium", "high"}


def assess_exposure(exposure: dict | None) -> str:
    """Classify exposure without summing ordinal judgements into a false numeric score."""
    exposure = exposure or {}
    values = [exposure.get(name) for name in EXPOSURE_DIMENSIONS]
    if any(value not in EXPOSURE_LEVELS for value in values):
        return "NEEDS_ASSESSMENT"
    highs = sum(value == "high" for value in values)
    mediums = sum(value == "medium" for value in values)
    # Coordination span and blast radius share an evidence base: "three independently released
    # consumers" reads high on both. So breadth alone could supply two of the three highs the
    # count clause needs, and one unrelated high would then tip a stable, low-criticality region
    # to HIGH. The count clause therefore also requires criticality or volatility to be high.
    # The two named clauses are untouched, which is why both worked entries stay HIGH.
    consequence_high = exposure["criticality"] == "high" or exposure["volatility"] == "high"
    if (
        exposure["criticality"] == "high"
        and exposure["coordination_span"] == "high"
    ) or (
        exposure["criticality"] == "high"
        and exposure["blast_radius"] == "high"
    ) or (highs >= 3 and consequence_high):
        return "HIGH"
    if highs >= 1 or mediums >= 2:
        return "MODERATE"
    return "LOW"


def decompose(metric: str, d: dict) -> tuple | None:
    """(numerator, denominator, human_detail) for a ratio metric, from a snapshot dict.
    None when the metric is not a ratio or the snapshot lacks the raw counts (old Snapshot)."""
    spec = DECOMPOSITIONS.get(metric)
    if not spec:
        return None
    nk, dk, nl, dl = spec
    if nk not in d or dk not in d:
        return None
    return d[nk], d[dk], f"{d[nk]} {nl} / {d[dk]} {dl}"


@dataclass
class Breach:
    metric: str
    ceiling: float
    observed: float
    # decomposition of the observed value, when the metric is a ratio (additive; default-empty
    # keeps old constructors working)
    numerator: float | None = None
    denominator: float | None = None
    detail: str = ""

    @property
    def delta(self) -> float:
        return round(self.observed - self.ceiling, 4)


@dataclass
class Budget:
    ceilings: dict[str, float]
    # Raw numerator standing behind each ratio ceiling when that ceiling was set. A ratio ceiling
    # alone cannot tell an improvement from a growing denominator, so the pawl consults these
    # before it drops a ceiling (see `tighten`). Absent for a legacy 0.2.0 budgets file.
    numerators: dict[str, float] = field(default_factory=dict)
    # Who set these ceilings, when, why, and what they replaced. The budgets file is the only
    # artefact CI enforces, so it is the one artefact that must not be authorless.
    provenance: dict = field(default_factory=dict)

    @classmethod
    def from_snapshot(cls, snap, *, author: str | None = None, reason: str | None = None,
                      set_at: str | None = None, prior: dict | None = None) -> "Budget":
        # Accepts a function-level Snapshot or a composite (anything with .to_dict()).
        # Watches only the WATCHED metrics actually present, so the same ratchet handles the
        # duplication-only Snapshot and the full portfolio without code changes.
        d = snap.to_dict()
        ceilings = {m: d[m] for m in WATCHED if m in d}
        prov = {}
        if author is not None:
            prov["author"] = author
        if reason is not None:
            prov["reason"] = reason
        if set_at is not None:
            prov["set_at"] = set_at
        if prior:
            prov["prior"] = prior
        return cls(ceilings=ceilings, numerators=numerators_for(ceilings, d), provenance=prov)

    @classmethod
    def load(cls, path: str) -> "Budget":
        # A budgets file that is missing or malformed is a configuration mistake, and the reader
        # needs the path and the remedy, not a traceback. The CLI turns these into exit 2.
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
        except FileNotFoundError:
            raise BudgetMissing(
                f"no budgets file at {path}; run `coherence-ratchet init` to write one"
            ) from None
        except json.JSONDecodeError as exc:
            raise BudgetMalformed(f"{path} is not valid JSON: {exc}") from None
        # A 0.2.0 budgets file carries `ceilings` alone. Accept it: an early adopter's CI must not
        # break on a schema addition. Without remembered numerators the pawl declines to tighten
        # a ratio it cannot verify, which is the safe direction.
        if not isinstance(raw, dict) or "ceilings" not in raw:
            raise BudgetMalformed(
                f"{path} has no `ceilings` key; it was not written by `coherence-ratchet init`"
            )
        return cls(
            ceilings=raw["ceilings"],
            numerators=raw.get("numerators", {}) or {},
            provenance=raw.get("provenance", {}) or {},
        )

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        payload: dict = {"ceilings": self.ceilings}
        if self.numerators:
            payload["numerators"] = self.numerators
        if self.provenance:
            payload["provenance"] = self.provenance
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")

    def breaches(self, snap) -> list[Breach]:
        d = snap.to_dict()
        out = []
        for m in self.ceilings:
            if m in d and d[m] > self.ceilings[m]:
                dec = decompose(m, d)
                num, den, detail = dec if dec else (None, None, "")
                out.append(Breach(metric=m, ceiling=self.ceilings[m], observed=d[m],
                                  numerator=num, denominator=den, detail=detail))
        return out

    def improvements(self, snap) -> dict[str, tuple[float, float]]:
        d = snap.to_dict()
        return {
            m: (self.ceilings[m], d[m]) for m in self.ceilings if m in d and d[m] < self.ceilings[m]
        }


def numerators_for(ceilings: dict[str, float], d: dict) -> dict[str, float]:
    """The raw numerator behind each ratio ceiling, where the snapshot reports one."""
    out = {}
    for m in ceilings:
        spec = DECOMPOSITIONS.get(m)
        if spec and spec[0] in d:
            out[m] = d[spec[0]]
    return out


class BudgetExists(Exception):
    """Raised when `init` would overwrite ceilings that already exist."""


class BudgetMissing(Exception):
    """Raised when the budgets file named on the command line is not there."""


class BudgetMalformed(Exception):
    """Raised when the budgets file exists but is not one this tool wrote."""


def init_budget(root: str, budgets_path: str, repo: str | None = None, *,
                author: str | None = None, reason: str | None = None, set_at: str | None = None,
                force: bool = False) -> Budget:
    """Write the baseline ceilings. Refuses to replace an existing budgets file unless forced.

    Re-baselining is how worsening enters without a signed decision, so it is an explicit act:
    it needs `force`, it needs an author and a reason, and it records the ceilings it replaced.
    """
    from .signals import measure_all

    prior = None
    if os.path.exists(budgets_path):
        if not force:
            raise BudgetExists(budgets_path)
        try:
            prior = Budget.load(budgets_path).ceilings
        except (OSError, ValueError, KeyError):
            prior = None

    budget = Budget.from_snapshot(measure_all(root, repo=repo), author=author, reason=reason,
                                  set_at=set_at, prior=prior)
    budget.save(budgets_path)
    return budget


def tighten(budget: Budget, snap, *, by: str | None = None,
            at: str | None = None) -> tuple[Budget, dict[str, str]]:
    """Ratchet the ceilings down to meet an improved measurement.

    A ratio can fall because the numerator shrank (a real improvement) or because the denominator
    grew (more code, the same mess). Under AI authorship the second is common, so the pawl consults
    the raw numerator recorded beside each ratio ceiling and declines to lower a ceiling whose
    numerator did not also hold or fall. Printing the counts beside the ratio is not the same as
    enforcing them; this is the enforcement.

    Returns the new budget and, for each metric it refused, the reason.
    """
    d = snap.to_dict()
    new: dict[str, float] = {}
    declined: dict[str, str] = {}
    held: set[str] = set()

    # An empty reading is not an improvement. `resolve_root` refuses an unmeasurable tree before
    # any of this runs, so reaching here with nothing measured means something upstream returned a
    # zero snapshot by another route. Every ratio would read 0.0 and every ceiling would ratchet to
    # zero, destroying the budgets file. Decline the whole pass and say why.
    #
    # The test is "this snapshot claims to have measured, and measured nothing", not "these keys are
    # absent": a partial snapshot that carries neither key is not a whole-tree reading and is not
    # this guard's business.
    total_functions, n_modules = d.get("total_functions"), d.get("n_modules")
    claims_a_tree = total_functions is not None or n_modules is not None
    if claims_a_tree and not (total_functions or 0) and not (n_modules or 0):
        return budget, {
            m: "measured zero functions and zero modules; an empty reading is not an improvement"
            for m in budget.ceilings
        }

    for m, ceiling in budget.ceilings.items():
        if m not in d or d[m] >= ceiling:
            new[m] = ceiling
            # This metric did not improve, so its ceiling stands and its remembered numerator must
            # stand with it. Refreshing it here let a worsening launder itself over two runs: hold
            # the ratio at its ceiling while the count climbs (numerator quietly rewritten upward),
            # then grow the denominator so the ratio dips, and the pawl compares against the
            # inflated count and tightens. The count ends worse and the ceiling ends lower.
            held.add(m)
            continue
        spec = DECOMPOSITIONS.get(m)
        prior_num = budget.numerators.get(m)
        if spec and spec[0] in d:
            observed_num = d[spec[0]]
            if prior_num is None:
                declined[m] = (
                    f"no recorded {spec[2]} count to compare against "
                    f"(observed {observed_num} {spec[2]}); re-run init to record one"
                )
                new[m] = ceiling
                continue
            # The count must have improved too, not merely held. A flat numerator with a grown
            # denominator is the dilution case exactly: the same number of cyclic modules, more
            # modules to divide by, a ratio that falls with nothing healed.
            if observed_num >= prior_num:
                moved = "rose" if observed_num > prior_num else "held at"
                shown = f"{prior_num:g} -> {observed_num:g}" if observed_num > prior_num else f"{observed_num:g}"
                declined[m] = (
                    f"{spec[2]} {moved} {shown} while the ratio fell {ceiling:g} -> {d[m]:g}; "
                    "the denominator grew, the structure did not improve"
                )
                new[m] = ceiling
                continue
        new[m] = d[m]

    kept = {m: v for m, v in budget.numerators.items() if m in declined or m in held}
    fresh = numerators_for(
        {m: v for m, v in new.items() if m not in declined and m not in held}, d)

    # The ceilings are the one artefact CI enforces, so the file has to say who moved them. Carrying
    # the baseline provenance forward unchanged named whoever took the baseline and never whoever
    # lowered it, which leaves a tightened ceiling unattributable: the honest-metric argument rests
    # on provenance tracking ceiling movement, not only ceiling creation.
    provenance = dict(budget.provenance)
    lowered = {m: (budget.ceilings[m], new[m]) for m in new
               if m in budget.ceilings and new[m] != budget.ceilings[m]}
    if lowered:
        event = {"metrics": {m: {"from": a, "to": b} for m, (a, b) in sorted(lowered.items())}}
        if by is not None:
            event["by"] = by
        if at is not None:
            event["at"] = at
        provenance["tightened"] = list(provenance.get("tightened", [])) + [event]

    return Budget(ceilings=new, numerators={**kept, **fresh}, provenance=provenance), declined


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
    exposure: dict | None = None,
    evidence: list[str] | None = None,
    confidence: str | None = None,
    review_date: str | None = None,
    status: str = "accepted",
    repayment_feasibility: str | None = None,
) -> None:
    """Append-only coherence-debt entry (JSON Lines)."""
    os.makedirs(os.path.dirname(ledger_path) or ".", exist_ok=True)
    entry = {
        "when": when,
        "region": region,
        "owner": owner,
        "repayment_trigger": repayment_trigger,
        "review_date": review_date,
        "status": status,
        "note": note,
        "exposure": {name: (exposure or {}).get(name) for name in EXPOSURE_DIMENSIONS},
        "exposure_tier": assess_exposure(exposure),
        "evidence": list(evidence or []),
        "confidence": confidence,
        "repayment_feasibility": repayment_feasibility,
        "breaches": [
            {
                "metric": b.metric, "ceiling": b.ceiling, "observed": b.observed,
                # decomposition travels with the ledger entry (additive; absent for count metrics)
                **({"numerator": b.numerator, "denominator": b.denominator, "detail": b.detail}
                   if b.detail else {}),
            }
            for b in breaches
        ],
    }
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def close_ledger_entry(ledger_path: str, *, region: str, when: str, by: str, reason: str) -> int:
    """Append a closing record for every open entry in a region. Returns how many were closed.

    The ledger stays append-only, so closing is a new record that supersedes rather than an edit.
    Without this the register could only grow, and a repaid item sat in it indefinitely looking
    like outstanding debt.
    """
    open_entries = []
    if os.path.exists(ledger_path):
        with open(ledger_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(entry, dict):
                    continue
                if entry.get("region") == region and entry.get("status", "accepted") != "closed":
                    open_entries.append(entry)
    if not open_entries:
        return 0
    with open(ledger_path, "a", encoding="utf-8") as f:
        for entry in open_entries:
            closing = dict(entry)
            closing.update({"when": when, "status": "closed", "closed_by": by,
                            "closed_reason": reason, "closes": entry.get("when")})
            f.write(json.dumps(closing, sort_keys=True) + "\n")
    return len(open_entries)

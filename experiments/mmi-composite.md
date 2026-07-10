# Experiment — Modularity Maturity Index (MMI) as a composite decay signal

**Direction:** B7 (corpus pass). Lilienthal's MMI (Software Architecture Metrics, Ch.4) is a validated
composite: **modularity 45% + hierarchy 30% + pattern consistency 25%**, reported as a maturity score
with tiers. This probe (`scripts/probe_mmi.py`) implements the three dimensions as deterministically as possible
over `archmetrics`, then asks: (1) does the composite discriminate the libraries; (2) do hierarchy and
pattern-consistency add signal beyond `cycle_ratio`; (3) does it corroborate flask's known decay?

## Result

**Current-state — the composite discriminates and matches the existing signal:**

| repo | MMI | tier | mod | hier | cons | cycle_ratio |
|---|---|---|---|---|---|---|
| boltons | 8.17 | low | 0.80 | 1.00 | 0.63 | 0.00 |
| httpie | 5.90 | high | 0.57 | 0.87 | 0.29 | 0.15 |
| requests | 3.37 | critical | 0.28 | 0.42 | 0.33 | 0.58 |
| flask | 3.22 | critical | 0.32 | 0.17 | 0.52 | 0.83 |

MMI ranks **boltons > httpie > requests > flask** — identical to the cycle_ratio ranking. So the
composite corroborates the first-party signal with an independent, published method, and adds a
**maturity-tier framing** (critical/high/moderate/low).

**Flask trajectory — MMI corroborates the decay:** 6.32 (2011, moderate) → 7.24 → 7.11 → 4.82 → 4.73 →
4.43 → 3.08 → 3.22 (2026, critical). The composite falls as flask ages, driven by modularity
(0.74 → 0.32) and hierarchy (1.0 → 0.17).

**The instructive part — the genuinely-new dimension is the one that isn't deterministic.** The
pattern-consistency proxy (`cons`) ranks differently from everything else: **boltons > flask >
requests > httpie**. Flask scores *high* consistency (0.52) despite being the worst overall — because
its modules are *uniformly* coupled (low instability variance). So the deterministic proxy rewards
"uniformly tangled" and is a **weak, sometimes-misleading** measure; across flask's history `cons`
stays flat/noisy (0.0–0.52) while the decay shows up entirely in modularity + hierarchy.

## What the book should take from this

- **Ch.5 (entropy budget):** adopt MMI's **maturity-tier framing** — the budget per region becomes a
  *maturity expectation* (critical/high/moderate/low), not just a numeric cap. Concrete and citeable.
- **Ch.6 / Appendix A:** MMI is an **external, published method that corroborates** the first-party
  decay curve — useful triangulation (the book's signal is not idiosyncratic). Its modularity +
  hierarchy dimensions largely overlap `cycle_ratio`/coupling, so MMI is mostly a *framing and
  corroboration* contribution there, not a new signal.
- **The key argument:** MMI's distinctive dimension — **pattern consistency** — is exactly the part that
  *cannot* be computed from the dependency graph. The cheap structural proxy is weak; real pattern
  consistency is *divergence from a sanctioned pattern*, which is the book's **catalogue / LLM gate**.
  So the most respected external composite, pushed to its hardest dimension, points straight back at
  the book's load-bearing artefact — a strong positioning point, not a gap.

## Honest caveats
- Sub-scores are rough-calibrated (same posture as `archmetrics`); absolute tiers are relative — e.g.
  "critical" for requests is harsh (cycle_ratio is inflated by `__init__` re-export edges). The
  **trajectory** (flask declining) and **cross-repo discrimination** (boltons healthy) are the robust
  parts, not the absolute numbers.
- Lilienthal's real MMI uses reviewer pairs + tool-assisted judgement across many criteria; this is a
  deterministic approximation of three headline dimensions, not the full instrument.
- Pattern consistency is a proxy only; n = 4 libraries; Python-AST limits as elsewhere.

## Artefacts
- `scripts/probe_mmi.py` — MMI dimensions over `archmetrics`; current-state + `--hist` flask trajectory.

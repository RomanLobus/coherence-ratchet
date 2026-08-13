# Experiment — change-driver (git co-change) guard on consolidation

**Direction:** B5 (corpus pass). Clean Architecture's **Common Closure Principle** (Martin, Ch.13)
and the SRP "accidental duplication" framing (Ch.7) say: consolidate only code that **changes for the
same reason**. Two look-alike functions with *different* change drivers must stay separate — merging
them creates a false shared dependency that explodes when they diverge. The behaviour-complete proof
(Ch.9) cannot see this: it verifies a merge preserves *current* behaviour, not that the merge couples
two things that should evolve independently.

**Probe (`probe_cochange.py`):** run the function-level duplication detector on three real libraries;
for every cluster whose members span ≥2 files, compute the **git co-change** of those files (Jaccard
of their full-history commit sets). Question: does co-change separate "safe to consolidate" (members
evolve together) from "leave divergent" (different change drivers)?

## Result — co-change discriminates, and adds an axis the detector is blind to

| Repo | cross-file cluster | co-change | what it actually is | right call |
|---|---|---|---|---|
| flask | `_make_timedelta` × 2 (app.py ↔ sansio/app.py) | **0.94** | private helper copied in the sansio split, evolves in lockstep | **consolidate** |
| flask | `send_static_file`, `open_resource`, `template_filter`, decorators (app ↔ blueprints) | 0.12 | deliberate App/Blueprint API mirror | leave |
| requests | HTTP verbs `get/post/put/...` (api.py ↔ sessions.py) | 0.09 | intentional API symmetry (already a known case) | leave |
| httpie | `pre_process` × 2 (v3_1_0 ↔ v3_2_0 legacy session formats) | 0.50 | deliberately frozen versioned migration shims | leave |

The duplication detector flags **all** of these identically as "the same idea, implemented again."
It cannot tell the accidental copy from intentional symmetry or versioned snapshots. **Co-change adds
that axis, orthogonally to the behaviour-proof:** the one cluster that changes in near-lockstep
(flask `_make_timedelta`, 0.94) is the textbook CCP violation to DRY; the deliberate API-symmetry
clusters sit far lower (0.09–0.12) and should be left exactly as they are.

## The honest nuance — it is a prioritiser, not an oracle

httpie's `pre_process` pair co-changes a moderate 0.50 yet should still be **left** — the two files are
intentionally-frozen versioned legacy shims (they were *added* together, hence the co-change, but each
pins a specific historical format). So co-change does not auto-decide; it **ranks** consolidation
pressure and surfaces the strongest candidates to the steward, who still applies the versioned/legacy
and intentional-symmetry exceptions. This matches the method's standing posture: instruments surface,
the human judges.

A second nuance: *low* co-change is ambiguous — it can mean "different change drivers (leave)" or
merely "both are stable and rarely change at all." It is **high** co-change that is the clear,
actionable signal (consolidate); low co-change lowers priority rather than proving independence.

## What the book should take from this

- **Ch.9 (paying down):** before the integrator merges a flagged duplicate, gate on co-change —
  prioritise high-co-change clusters (genuine accidental copies that drift in lockstep) and do **not**
  auto-merge zero/low-co-change duplicates (likely intentional symmetry or independently-evolving
  look-alikes). This is a cheap, deterministic pre-filter that runs before the (expensive)
  behaviour-complete proof and catches a failure mode the proof structurally cannot.
- **Ch.5 (entropy budget):** the budget already weighs *factorability* and *volatility*; **co-change
  is a concrete, computable measure of "do these change together,"** sharpening the repayment trigger
  (consolidate what co-changes and is factorable; leave what does not).
- **Ch.10 (dead-ends):** strengthens the existing "consolidate everything / dedup-is-always-good"
  discard with a positive instrument — co-change shows *which* duplicates are worth it.
- Connects to the existing requests "intentional API symmetry" finding: the verbs score low co-change,
  giving a quantitative reason to leave them that the gate previously had to reason about semantically.

## Honest caveats
- Co-change via `git log --follow` per file; rename history is imperfect, and a file's commit set
  mixes all reasons it ever changed (coarse — file-level, not function-level, co-change).
- n = 3 libraries; few cross-file clusters survive the structural threshold (the divergent-but-same
  reimplementations the structural detector misses would need the semantic detector first, then this
  guard on the result).
- "Should consolidate / leave" labels are the author's reading of each case, not ground truth.
- Single snapshot of current HEAD; the legacy/versioned exception (httpie) shows domain knowledge
  still overrides the metric.

## Artefacts
- `probe_cochange.py` — reuses `coherence_ratchet.metrics` internals; per-cluster co-change over git history.

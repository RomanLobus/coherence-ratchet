# Experiment — combined consolidation-priority score (connascence × co-change)

**Direction:** P9 (fuses P2 + P3). P2 (co-change) is the *empirical* "does change together"; P3
(connascence locality × degree) is the *structural* "would have to change together." Each alone is
flawed — connascence is dominated by degree (so it ranks high-fan-out intentional symmetry highly),
and co-change gives no structural priority magnitude and is ambiguous at the low end. This probe
(`scripts/probe_priority.py`) multiplies them into one ranking and tests whether the product prioritises the
genuine accidental copy while demoting deliberate symmetry, beating either signal alone.

## Result — the product orders correctly where each signal alone fails

Flask (the only library with enough cross-file clusters to rank):

| ranking | #1 | #2 | #3 | verdict |
|---|---|---|---|---|
| connascence-alone (loc × deg) | `app_template_filter` (12) | `decorator` (12) | `_make_timedelta` (6) | **wrong** — intentional App/Blueprint mirrors on top; the real copy 3rd |
| co-change-alone | `_make_timedelta` (0.94) | mirrors (0.12) | mirrors (0.12) | right target, but no structural magnitude; mirrors undifferentiated |
| **combined (loc × deg × co-change)** | **`_make_timedelta` (5.65)** | mirrors (1.39) | mirrors (1.39) | **correct** — genuine accidental copy #1, deliberate symmetry demoted |

Connascence-alone *inverts* the ranking (degree pushes the deliberate `template_*`/`decorator` mirror
families above the genuine copy). Co-change-alone picks the right #1 but gives every deliberate mirror
the same low score with no sense of structural weight. The **product** puts the real consolidation
target (`_make_timedelta`, copied across the app↔sansio split, evolving in lockstep) clearly first and
pushes the intentional API symmetry down — the ranking a steward actually wants. (requests and httpie
each have a single cross-file cluster, so no ranking to discriminate; the score computes cleanly there.)

## What the book should take from this

- **Ch.9 (paying down) + Ch.5 (budget):** ship a single **consolidation-priority score** =
  locality × degree × co-change. It encodes both halves of the Common-Closure test — *structural*
  coupling strength and *realised* change-coupling — so the integrator and the steward work a ranked
  list whose top is genuinely worth consolidating, not the highest-fan-out deliberate pattern.
- It also gives the entropy budget a concrete prioritiser: spend the consolidation budget top-down
  this list; everything below a threshold is bounded decay left on purpose.
- Reinforces P2/P3/P6: structural signals propose, the realised (empirical) signal disposes, and the
  human still owns the versioned/legacy exceptions co-change cannot see.

## Honest caveats
- Only flask had enough cross-file clusters (6) to demonstrate re-ranking; n is small.
- Deterministic structural duplication only — the divergent reimplementations the AST detector misses
  (and P8's evasions) would need the semantic detector *first*, then this score on the result.
- The product weighting (plain multiply, locality 1/2/3) is untuned; the ordering is robust to it here
  but the absolute scores are not calibrated.
- "Correct ranking" is the author's reading of which flask clusters are genuine vs intentional.

## Artefacts
- `scripts/probe_priority.py` — reuses `probe_cochange` (co-change) and `probe_connascence` (locality) internals.

# Experiment — Does the ratchet mechanism transfer to architecture-level signals?

**Question:** the function-level ratchet works (baseline the existing redundancy, allow hold-or-lower, block backsliding). Does the same delta mechanism work on architectural signals (cycle_ratio, coupling) — would it have caught the decay the longitudinal study found?

**Result: yes, the delta/ratchet logic transfers cleanly — applied to `cycle_ratio` it would have arrested the monotonic architectural decay (flask 0.0 → 0.83 was 30 of 43 un-arrested small increases). But the honest framing matters: the baseline must be *current-state*, not zero; not every cycle is bad, so it surfaces to a steward rather than mandating zero; and the coupling-misfire risk was under-tested here, so cycle_ratio is the ratcheted signal and coupling stays diagnostic.**

## What was run
Densely sampled each repo's history (~43–50 commits), measured `cycle_ratio` and `coupling` at each, and applied ratchet logic: a running floor that only lowers; an interval that raises cycle_ratio past the floor is "flagged" (backsliding); one that lowers it is an allowed consolidation.

| Repo | cycle_ratio baseline → actual final | Intervals the ratchet would FLAG | Consolidations allowed | Coupling-misfire events |
|---|---|---|---|---|
| flask | 0.00 → **0.83** | 30 / 43 | 0 | 0 |
| requests | 0.00 → **0.58** | 48 / 49 | 0 | 0 |
| httpie | 0.00 → 0.15 | 38 / 50 | 1 | 0 |

## What it shows
- **The decay was a series of small, un-arrested increases — exactly what a ratchet catches.** flask did not tangle in one bad commit; cycle_ratio crept up across most sampled intervals with essentially no consolidation pulling it back (0 consolidations for flask and requests at this granularity). A ratchet enforcing "hold or lower" on cycle_ratio would have surfaced each increase for a decision instead of letting them accumulate to 0.83. The mechanism that works for function redundancy works for architectural structure.
- **It is a delta instrument here too.** The signal that matters is the *change* in cyclic structure from a baseline, not an absolute target — the same refinement the function ratchet needed.

## Honest framing (where the clean numbers mislead)
- **A 0.0 baseline is unrealistic.** I baselined at each project's earliest (tiny) state, which inflates the flag count — much of the early cycle growth is a young framework legitimately growing an interdependent core, not decay. The realistic use is the function ratchet's rule: **baseline the *current* state and forbid backsliding.** Baselined at, say, mature-flask's 0.43, the ratchet would have held ~0.43 and flagged only the ~dozen later increases that took it to 0.83 — which is the right behaviour. The trajectory holds under any baseline (it climbs monotonically), so the conclusion stands; the flag *count* is an artefact of the zero baseline.
- **Not every cycle is bad.** Some module interdependence is legitimate. So the ratchet *surfaces* a cycle-increasing change to the steward (as the function gate surfaces, never auto-blocks); it is not a mandate of zero cycles.
- **The coupling-misfire risk was under-tested, not cleared.** 0 misfire events only because there were almost no consolidation intervals to check (cycles rarely fell at this sampling). The function-level finding stands as the prior: healthy consolidation can *raise* coupling (merging modules adds edges), so **coupling stays a diagnostic, and `cycle_ratio` is the ratcheted signal.** This experiment does not overturn that — it had too few consolidations to probe it.

## Honest caveats
- Sampled (not per-commit) granularity, so consolidation events are undercounted (httpie's real 2020 de-cycling refactor showed as just 1 allowed consolidation). A per-commit run would show consolidation better but is slower.
- `cycle_ratio` calibration is rough (`__init__` re-exports); the ratchet acts on the *trend*, which is robust.
- Retrospective simulation, not a live ratchet on a real team — it shows the signal would have fired, not that a team would have acted.

## Verdict
The ratchet generalises to the architecture level: enforcing hold-or-lower on `cycle_ratio` from a current-state baseline would have surfaced flask's and requests' steady cycle growth instead of letting it compound — the decay was precisely the un-ratcheted accumulation a ratchet exists to stop. The architectural ratchet uses `cycle_ratio` as its pawl, keeps coupling as a diagnostic (misfire risk intact, just untriggered here), baselines current-state rather than chasing zero, and surfaces increases to a steward. This is the function ratchet's logic, one level up.

→ book: Ch.7 — the ratchet's headline signal is architectural (cycle/coupling delta from a current-state baseline), with coupling diagnostic; the decay curves (architecture-decay.md) are the "what happens without it" and this is the "what the ratchet would have done." Dead-end reaffirmed at the architecture level: "ratchet an absolute score / mandate zero cycles" — no; baseline current-state, surface backsliding, leave legitimate interdependence.

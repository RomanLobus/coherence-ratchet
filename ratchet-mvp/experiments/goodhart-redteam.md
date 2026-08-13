# Experiment — Goodhart red-team on the cycle_ratio ratchet

**Direction:** B11 (corpus pass). Software Architecture Metrics Ch.7 warns that a metric optimised as a
target stops measuring the thing you care about. The book's headline ratchet gates on `cycle_ratio`.
This probe asks: can a system **pass the cycle gate while fragmenting on the axes the gate ignores**
(duplication, connascence of meaning)? Five agents implemented three features (each needing
cents-conversion + retry) in isolated copies of a tiny `shop` package whose canonical helpers
(`money.to_cents`, `net.with_retry`) already existed; the only stated gate was "no new import cycles."

## Result — the gate is structurally blind to additive fragmentation

| State | cycle_ratio (GATE) | dup_ratio | connascence of meaning |
|---|---|---|---|
| baseline | 0.0 | 0.0 | — |
| 5 agent trials (helpers visible) | **0.0 (pass)** | 0.375 | low |
| fragmented variant (helpers reinvented) | **0.0 (pass)** | 0.60 | `'0.01'` rounding literal across 4 modules; retry `3` across 4 |

Two findings:

1. **The cycle-only gate gives false assurance.** A fully fragmented version — every `to_cents` and
   retry loop reinvented inline, the exact AI additive failure mode — sails through the gate at
   `cycle_ratio 0.0` while duplication hits 0.60 and the **rounding mode (`ROUND_HALF_UP`/`'0.01'`)
   becomes an implicit agreement scattered across four modules**. That is the precise risk the
   integrator probe flagged (a silent rounding-mode change): the gate that is supposed to protect
   coherence cannot see it, because additive duplication never creates a cycle. Cycles and duplication
   are orthogonal axes (already shown in `architecture-decay.md`); gating on one proves nothing about
   the other.

2. **Agents in-context did not actually game it — they reused.** All 5 trials *found and imported* the
   canonical helpers (the package was small enough to see), so real metric-gaming did not occur here;
   the gate simply was never stressed. This is the project's standing "legible + in-context → reliable"
   meta-finding again: the Goodhart danger is not that agents cynically game the gate, it is that the
   gate is **blind by construction**, so passing it carries no information about the dominant failure
   mode — which bites at scale, where the helper is *not* visible and fragmentation happens for the
   ordinary visibility reason. (Even the reuse trials scored dup 0.375: the three feature functions
   share an orchestration shape the cycle gate also cannot see.)

## What the book should take from this

- **Ch.10 (dead-ends) + Ch.6:** add "ratcheting a single metric" as a discard. A cycle-only ratchet
  is satisfiable by a fully fragmented system; the headline signal must be **multi-signal** —
  duplication / connascence / cycles watched together (this is the fitness-function portfolio, B8).
- **Ch.7:** the ratchet is a *portfolio* of delta checks across orthogonal axes, not one number.
  Frames the Goodhart risk explicitly and answers it.
- Reinforces "visibility is the lever": the gate does not create reuse; surfacing the helper does
  (the trials reused because they could see it).

## Honest caveats
- n = 5 agent trials + one hand-built fragmented variant; tiny package (the legibility is exactly why
  agents reused — a larger codebase is the untested regime, named not demonstrated).
- The fragmented variant is author-constructed to model the out-of-context case; it is an existence
  proof that the gate passes a fragmented system, not a measured agent rate.
- Connascence-of-meaning detection is the same flood-prone proxy as in `connascence-signal.md`.

## Artefacts
- `scratchpad/p4/` — baseline, 5 agent trials, fragmented variant; measured with `metrics` +
  `archmetrics` + `probe_connascence`.

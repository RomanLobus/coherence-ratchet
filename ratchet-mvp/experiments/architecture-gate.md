# Experiment — LLM architecture-coherence gate (the semantic half of architecture)

**Hypothesis:** the structural metric (`archmetrics.py`) catches what the *import graph* reveals — cycles, coupling, fan-in. But the architectural smells that matter most are often *semantic*: a layering violation (which edge is "wrong" depends on which module is high vs low), a misplaced responsibility (a model doing network I/O). Those are invisible in the import graph alone. Can an LLM catch them — the architecture-level analogue of the semantic function detector?

**Result: perfect recall on all three injected smells (6/6 trials each), including the two the structural metric cannot see — but the gate is chattier than the function-level one (~0.8 extra findings/trial), so it needs constraining to a stated layering spec, exactly the catalogue discipline the function gate required.**

## Design
A 10-module layered architecture (handler > service > repository > model > util) presented as a manifest (name, layer, one-line responsibility, dependencies). Three injected smells an import-graph metric would *not* flag as wrong, plus seven clean modules. 6 trials, asked to find layering violations, misplaced responsibilities, and god modules.

| Injected smell | Module | Can `archmetrics` see it? | Caught |
|---|---|---|---|
| Layering violation (util depends *up* on a handler) | `string_utils` | **No** — needs layer semantics | **6/6** |
| Misplaced responsibility (a model sends SMTP email) | `order_model` | **No** — needs responsibility semantics | **6/6** |
| God module (7 unrelated concerns, high fan-in) | `helpers` | Yes — `max_fan_in` | **6/6** |

False-positive findings (implicating only clean modules): mean **0.8/trial**.

## What it shows
- **The LLM catches the semantic architectural smells the structural metric is blind to.** Layering violations and misplaced responsibilities require knowing what a module *is for* and where it sits — not just who imports whom. The LLM got both, every trial, and explained them correctly (e.g., "a util must not reach up into a handler"; "sending email is service-level I/O, not a model's job, and an email_service already exists"). This is the architecture-level mirror of the function-level result: structural detection plus an LLM semantic pass covers what either misses alone.
- **The two-layer pattern holds at the architecture level.** Deterministic `archmetrics` for the structural signals (cycles/coupling/fan-in, cheap, language-bound), LLM gate for the semantic ones (layering/responsibility, language-agnostic). Same funnel shape as the function detector.
- **Architectural reasoning is inherently language-agnostic.** The gate reasons over modules, responsibilities, and dependencies — not syntax — so unlike code-level clustering it carries across languages by construction. The manifest representation has no language at all.

## The honest weakness: it over-reports
The ~0.8 false findings per trial were not hallucinations — they were defensible *extra* opinions the prompt did not ask for: "apply auth as cross-cutting middleware rather than wiring it into the handler," "put the payment adapter behind an interface." Reasonable architecture advice, but un-requested, and for a gate that surfaces to a steward it is noise. This is exactly the failure mode the function-level work already diagnosed: open-ended "review the architecture" invites the model to editorialise. The fix is the same — **constrain it to objective matching against a stated layering spec / sanctioned-pattern catalogue** ("does this violate *these* declared layer rules?") rather than open judgment. The architecture gate needs its catalogue just as the function gate did.

## Honest caveats
- Hand-crafted 10-module manifest with clearly-injected smells — the easy case (as with E2/H5). Subtle real-world architectural smells, and larger systems where the manifest itself is hard to assemble, are untested.
- Recall 6/6 on three smells; precision measured loosely (the "extra" findings are reasonable, not wrong, so 0.8/trial overstates true error). A catalogue-constrained version would measure precision properly.
- n=6, Claude, single architecture.

## Verdict
The LLM architecture-coherence gate works for recall — it catches layering violations and misplaced responsibilities the import-graph metric cannot, 6/6 — completing the architecture-level detector as a two-stage funnel (structural `archmetrics` + semantic LLM). It over-reports reasonable extras, so it carries the same constraint the function gate does: bind it to a declared layering spec and surface to a steward, never auto-act. Architecture reasoning being language-neutral is a bonus — this layer crosses languages by construction.

## Follow-up — constraining the gate to a declared layering catalogue
The over-reporting has the same fix as the function gate: give the LLM the *declared* rules and ask it to flag only violations of those. Re-run with an explicit catalogue (R1 layering order; R2 no I/O below services; R3 single-purpose utils):

| | Recall (3 injected) | False-positive findings/trial |
|---|---|---|
| Open-ended "review the architecture" | 3/3, 6/6 | **0.8** (auth-as-middleware, payment-behind-interface — reasonable extras) |
| Catalogue-constrained "flag only R1–R3 violations" | 3/3, 6/6 | **0.2** (one benign "no violation here" note) |

Constraining to the declared layering spec **held recall and cut the editorialising to near-zero** — the architecture-level replication of the function-level result that the LLM works as an *objective matcher against a curated catalogue*, not an open judge. The layering spec is that catalogue. (It correctly applied R2 to `helpers` too — its HTTP client is util-level I/O — which is a true extra catch, not noise.)

→ book: Ch.6/Ch.7 — the detector is two-stage at the architecture level too (structural cycles/coupling + semantic layering/responsibility); the **layering spec is the architectural catalogue** the gate matches against (ties to the structure-spec, Ch.3), and constraining to it tightens precision exactly as the function catalogue did. Reinforces the standing rule: LLM as constrained matcher + human steward, never open-ended judge.

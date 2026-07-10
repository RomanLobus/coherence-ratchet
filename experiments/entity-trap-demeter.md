# Experiment — Entity Trap and Law-of-Demeter coupling redistribution

**Direction:** B12 (corpus pass). Fundamentals Ch.8 names two ideas the book had not used: the
**Entity Trap** (organising components around entities — `Order`, `Customer` — produces god-modules
that violate SRP) with the claim that LLMs are *prone* to it; and the **Law of Demeter** lesson that
moving knowledge to a coordinator *redistributes* coupling rather than removing it. Two probes.

## Part (a) — Entity Trap: NOT confirmed for current single-agent builds

Four independent agents each built the same small order system (place / cancel / ship / invoice),
free to structure modules however they liked. Result — **all four separated responsibilities; none
produced an entity god-module:**

| agent | modules |
|---|---|
| 1 | models, repository, pricing, orders, shipping, invoicing |
| 2 | models, repository, pricing, notifications, invoicing, orders (+DI) |
| 3 | models, repository, orders, shipping, invoicing |
| 4 | models, repository, pricing, place_order, cancel_order, shipping, invoice |

Every agent split a data-only `models.py`, a `repository.py` for persistence, a shared `pricing.py`,
and per-workflow modules. That is **responsibility-separated, not entity-trapped** — the opposite of a
god-module. So the corpus hypothesis "LLMs are prone to the Entity Trap" is **not supported** here;
current Claude agents modularise sensibly within a single coherent task.

The real entity risk is elsewhere and already established: **cross-agent entity divergence** —
independent agents producing mutually-incompatible `Order` schemas (`entity-coherence.md`, 5/5 distinct
schemas). The danger is between independent authors/sessions, not within one agent's module layout.

**Book impact:** do *not* claim LLMs fall into the Entity Trap (the evidence here refutes it for
in-task builds). Keep the entity-coherence risk framed as a *cross-agent / cross-session divergence*
problem (Ch.6 signal, Ch.3 structure-spec pins canonical entity shapes) — which the convergence and
entity-coherence experiments already support.

## Part (b) — Law of Demeter: consolidation redistributes coupling, measured

Same fragmented `shop` from the Goodhart probe, in two states:

| state | internal edges | max fan-in | dup_ratio |
|---|---|---|---|
| fragmented (each module reinvents to_cents + retry) | **0** | 0 | 0.60 |
| consolidated (each imports the shared `money`/`net` helpers) | **6** | **3** | 0.375 |

Consolidating duplicate logic to shared helpers **traded duplication for coupling**: edges 0 → 6,
fan-in 0 → 3 (concentrated on `money`/`net`), duplication 0.60 → 0.375. The coupling did not vanish —
it **relocated into the helper**, which becomes a higher-fan-in node. This is exactly Page-Jones /
Demeter: you redistribute coupling, you do not eliminate it.

**Book impact:** (1) confirms *why* coupling is a **diagnostic, not a ratcheted metric** (the method's
existing stance) — healthy consolidation *raises* coupling, so ratcheting it would mis-fire; Ch.7.
(2) a caution for the integrator (Ch.9): aggressive consolidation to a central coordinator concentrates
fan-in (a god-helper), so the integrator should prefer leaf helpers and the steward should watch
fan-in concentration, not just duplication reduction.

## Honest caveats
- Part (a): n = 4, one domain, single-session builds; "no Entity Trap" is a claim about *current
  agents on a coherent task*, not all conditions. `archmetrics` read coupling 0 on these flat
  (non-package) dirs — an import-resolution limitation on non-package layouts — so the (a) finding is
  the **module-structure** evidence, not the (spurious) coupling number.
- Part (b): a deliberately small, legible fixture; the edge/fan-in counts are an existence proof of
  redistribution, not a magnitude claim.

## Artefacts
- `scratchpad/p6a/agent1..4` — independent order-system builds.
- `scratchpad/p4/{fragmented,trial1}` — the coupling-redistribution comparison.

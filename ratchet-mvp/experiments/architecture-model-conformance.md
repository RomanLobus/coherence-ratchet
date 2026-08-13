# Experiment #5 — Architecture-model conformance

**Hypothesis (open direction #5):** giving agents an explicit *architecture model* (declared modules + layering) — the system-level analogue of D5's function contract — makes their output conform: consistent structure, no cycles, no upward imports.

**Result: the model collapsed structural divergence — 4 distinct module layouts across free-form variants down to 1 identical layout under the model. But cycle-prevention was untriggered: free-form agents already produced acyclic, layered code for this small feature, so the measured payoff is consistency-by-construction, not cycle-avoidance (which the longitudinal study shows bites as systems grow, not at six modules).**

## Design
A small "place an order" feature (validate → persist → charge → orchestrate), implemented 8 times each:
- **Free-form:** the feature only.
- **Arch-model:** the feature plus a declared model — six modules (`order_handler` [handler] > `order_service`, `payment_service` [service] > `order_repository` [repository] > `validators`, `money` [util]) with the layering rule "import only your own layer or lower."

Each variant's files were assembled into a module graph; measured for layout consistency, dependency cycles, and upward (layering-violating) imports.

## Results

| | Distinct module layouts (8 variants) | Variants with a cycle | Upward-import violations | Module counts |
|---|---|---|---|---|
| Free-form | **4** | 0/8 | 0 | 7–9 (varied) |
| Arch-model | **1** | 0/8 | 0 | 6 (all identical) |

## What it shows
- **The model collapses structural divergence — the D5 result, one level up.** Free-form, eight competent agents produced four different module layouts (7–9 modules: some split an `errors.py`, some a `models.py`, some merged concerns). Under the declared model, all eight produced exactly the same six modules. Anything that depends on the system's structure — other modules, the ratchet's baseline, a reviewer's mental model — is now stable across contributions. This is the architecture-level form of "pin the contract and divergence vanishes."
- **The architecture model is the system-level structure-spec.** It is exactly the artefact Ch.3 proposes (the intended structure), shown here to bind agent output to a single shape. It composes with the ratchet (the model is the baseline the cycle/coupling delta is measured against) and the gate (the layering spec is the catalogue the gate matches).
- **Cycle-prevention was not the lever here — and that's honest.** Free-form agents created *no* cycles and *no* upward imports for a clean six-module feature. So for small, well-understood features the model buys consistency, not correctness. Its decay-prevention value is inferential and longer-horizon: the longitudinal study showed cycles and coupling accumulate as systems *grow over years* (flask 0→0.83); a maintained model that forbids the upward imports which create cycles would arrest that accumulation — but that is the multi-year claim the young/clean fixture cannot demonstrate, the same wall as the macro decay measurement.

## Honest caveats
- Small clean feature (6 modules), Claude/Python, 8 variants — the easy case, where free-form is already acyclic. The interesting test (does the model prevent cycle accumulation as a system grows to dozens of modules over time) is exactly the unmeasurable long-horizon regime.
- "Consistency" measured as identical module-name sets; deeper structural identity (same edges, same responsibilities per module) was not separately scored, though the single layout implies high agreement.
- A maintained architecture model is itself an artefact that must be kept current as the system legitimately evolves — the same staleness burden as the catalogue (R4).

## Verdict
An explicit architecture model works as a *consistency* lever: it took eight divergent module layouts to one, the system-level analogue of D5's contract scaffold, and it is precisely the structure-spec the method already proposes — now shown to bind multi-agent output to a single shape and to serve as the ratchet's baseline and the gate's layering catalogue. Its decay-prevention value (forbidding the upward imports that grow into cycles) is real in principle but longer-horizon than a clean small fixture can show — the same untestable macro regime as the architecture decay curve. The lever is constrain-by-design at the architecture level: pin the structure, regenerate beneath it.

→ book: Ch.3 (the structure-spec *is* an architecture model that collapses agent divergence — measured) and Ch.5/Ch.7 (the model is the ratchet's baseline and the gate's layering catalogue). Honest note: consistency is measured; cycle-prevention-at-scale is inferred, bounded by the same young-codebase limit.

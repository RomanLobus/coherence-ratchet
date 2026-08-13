# Experiment — Fitness functions as deterministic enforcement

**Why:** the book co-positions with *Architecture as Code* (Ford), whose mechanism is executable architecture **fitness functions**. This tests the relationship directly: can fitness functions enforce the structural/shape rules deterministically, and where is the boundary with the LLM gate?

**Result: fitness functions are the deterministic enforcement layer — they catch exactly the encodable structural and shape violations with no LLM, and the boundary is clean: rules you can express as code go to fitness functions; the semantic judgments you cannot go to the LLM gate. The ratchet is itself a fitness function on a delta.**

## Three fitness functions, run on existing fixtures

| Fitness function | Subject | Verdict |
|---|---|---|
| **No layering violations** (a lower layer must not import a higher one) | arch-gate manifest | **FAIL** — caught `string_utils[util] → checkout_handler[handler]` |
| **No dependency cycles** | boltons / flask | boltons **PASS**; flask **FAIL** (1 cycle, 20 modules tangled) |
| **Canonical entity shape** (all `Order` reps share one field set) | entity-coherence fixtures | fragmented (5 agents) **FAIL** — 5 distinct shapes; coherent (1 agent) **PASS** |

Each is a few lines of deterministic Python over the dependency graph / declared layers / extracted field sets. They fire precisely on the violations and pass the clean cases.

## What it means
- **Fitness functions enforce the encodable rules deterministically and cheaply.** Layering, acyclicity, canonical entity shape — anything expressible as a rule over the structure — is a fitness function: fast, no LLM, no flakiness, runnable in CI on every change. This is exactly the *Architecture as Code* enforcement mechanism, and it slots into the method as the deterministic floor of the **gate**.
- **The boundary with the LLM gate is clean and complementary.** Fitness functions cannot express the semantic judgments — "is this the same concept reimplemented divergently?", "is sending email a *misplaced* responsibility?", "is logging used *consistently*?" The LLM gate (constrained to a catalogue, multi-trial, surfaced to a steward) handles those. So the gate is two-layer: **fitness functions for the rules you can write down; the LLM for the rules you can only recognise.**
- **The ratchet is a fitness function on a delta.** "`cycle_ratio` may hold or fall, never rise from the baseline" is exactly a fitness function comparing two measurements. The ratchet is not a separate mechanism from fitness functions — it is the *delta* form of one, which is what makes it a continuous gate rather than a one-off absolute check.

## Honest caveats
- Each fitness function encodes a rule someone must author and maintain (the layer map, the canonical schema) — the same catalogue/structure-spec maintenance burden (R4); a fitness function is only as right as its declared rule.
- These are deterministic over *static* structure (imports, declared layers, extracted shapes); they cannot see runtime or semantic violations — by design, that is the LLM gate's half.
- Reuses prior fixtures rather than a fresh study; the point is the mechanism and its boundary, not a new rate.

## Verdict
Fitness functions are the deterministic enforcement layer the method already implied: they catch layering violations, cycles, and entity-shape divergence as cheap CI-runnable checks (Architecture-as-Code, exactly co-positioned), and the ratchet is their delta form. The clean division of labour — fitness functions for the writable rules, the LLM gate for the recognisable-but-unwritable ones, steward over both — is the gate's real architecture. This is less a new finding than the precise statement of how the method and *Architecture as Code* compose: the technique is the deterministic floor; the operating model adds the semantic gate, the steward, and the ratchet discipline on top.

→ book: Ch.7 (the gate is fitness-functions + LLM, two layers; the ratchet is a delta fitness function) and §6 (the precise composition with *Architecture as Code* — technique below, operating model above, now concretely demonstrated). Reinforces the catalogue-maintenance burden (R4) — a fitness function inherits its rule's staleness risk.

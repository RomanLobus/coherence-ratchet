# Reframe C — Multi-agent convergence (vs a central self-model)

**Question (the capstone counterpoint to A):** after building a centralised self-model + ratified canon, do you even need it — can *decentralised* convergence (agents see each other's proposals and negotiate) reach a shared shape on its own?

**Result: convergence does the bulk of the work but not the last mile. Six agents designing an Order schema went from 0.68 to 0.92 mean field-overlap after one round of seeing each other — near-consensus on substance — but stayed at 4 distinct schemas (not 1) because of cosmetic residuals (`status` vs `order_status`, `fulfilment` vs `fulfillment` spelling, optional `version`/`tracking_number`). So convergence is a strong *complement* (cheap pre-alignment), not a full *substitute* for a central ratified canon — the last-mile tie-break still needs one.**

## Results

| Round | Distinct schemas (of 6) | Mean pairwise field-overlap (Jaccard) |
|---|---|---|
| 1 — independent | 5 | 0.68 |
| 2 — after seeing each other | 4 | **0.92** |

One round of mutual visibility lifted overlap from 0.68 to 0.92 — the agents substantially agreed on the field set. The residual disagreement was **cosmetic, not structural**: a few naming choices (`status`/`order_status`), a spelling split (`fulfilment`/`fulfillment`), and a couple of optional fields (`version`, `tracking_number`).

## What it means
- **Agents converge most of the way on their own.** Seeing each other's proposals drove near-consensus (0.92 overlap) — consistent with B (the modal pattern is sound) and the cross-cutting finding (independent agents converged on stdlib logging). The canon is largely *emergent*; decentralised negotiation surfaces it cheaply.
- **But the last mile does not auto-resolve.** Convergence left 4 distinct schemas over trivial differences (a name, a spelling, an optional field) that no agent could unilaterally settle. That residue needs a **tie-break** — a central ratified canon (A's self-model + B's ratification) deciding "it is `status`, US spelling, include `version`."
- **So convergence is a complement, not a substitute.** It is a good *greenfield / no-model-yet* pre-alignment step (get to 0.92 cheaply), after which the ratified self-model pins the last mile. The central artefact (A+B) is still needed — but convergence reduces how much it has to impose.
- **The residue's cost depends on E's finding.** Cosmetic naming divergence (`status`/`order_status`) is cheap for an *AI* maintainer (E) — but it is exactly the kind of field-name mismatch that breaks interoperability at a contract boundary (entity-coherence `KeyError`). So the last-mile tie-break matters precisely *at contracts*, which is where the pivoted target says coherence must hold.

## Honest caveats
- One concept (Order schema) with strong shared priors — hence the high 0.68 baseline; a less conventional domain would converge less. n=6, one convergence round (more rounds might collapse further, or oscillate). Field-name level only (not deeper structure).
- "4 distinct" overstates real disagreement — the schemas are ~92% identical; the metric counts any difference, including a spelling. The honest read is *near-consensus with a cosmetic tail*, not failure to converge.

## Gate decision
**Convergence is a complement to the central self-model, not a replacement.** Use it as a cheap pre-alignment (especially greenfield, before a self-model exists); keep A+B as the authoritative last-mile tie-break, which matters most at contract boundaries (per E). For the chain, this positions A vs C in the book: emergent convergence does the bulk, the ratified self-model resolves the residue.

→ book: Ch.7/Ch.11 — decentralised convergence is a lightweight pre-alignment (agents see each other → 0.92 overlap), but the steward's ratified self-model still settles the cosmetic-but-interop-critical last mile (field names at contracts). Pairs with B (emergent canon) and E (the residue is cheap internally, costly at contracts).

# Reframe F — Cell / blast-radius design (synthesis)

**Not a new experiment — the architectural conclusion the chain forces.** E set the target; D5, D6, A, C supply the mechanism. F states the shape they imply.

**Synthesis: the coherence the AI era needs is at the *contract*, not inside the cell. Pin the interface; let the internals diverge and regenerate. Every probe in the chain points the same way.**

## The argument, assembled from the chain
- **E + E-b — *where* coherence costs.** Visible, non-breaking internal incoherence is cheap for an AI maintainer (8/8 = 8/8; 7/8 even with a site hidden). The cost concentrates at **contract/interoperability boundaries** (entity-coherence's `KeyError`) and at **independent sites beyond the context window**. So uniform internal coherence is not the goal; coherence *at the seams* is.
- **D5 — pinning the contract collapses divergence at the boundary.** A fixed contract took 4 divergent module layouts to 1. The boundary is exactly what a contract can hold.
- **D6 — internals beneath a pinned contract are disposable.** Regeneration diverges wildly from an intent-level spec but converges completely once a contract is fixed: the fill under a stable contract can be thrown away and regenerated.
- **A — the self-model makes the contracts (and divergent sites) visible.** It is the contract registry: it surfaces every site a cross-cutting change must touch (1/8 → 8/8), which is precisely how you keep the *seams* coherent at scale.
- **C — the last-mile tie-break that matters is at the contract.** Convergence aligns substance (0.92) but leaves cosmetic field-name residue; that residue is cheap internally (E) yet breaks interop at a boundary — so it must be pinned exactly *there*.

## The shape
**Cells with pinned contracts, disposable internals, coherence enforced at the seams.**
- A unit (module/service/"cell") exposes a **pinned contract** — its interface and the entity shapes it exchanges — captured in the structure-spec and held in the derived self-model. This is where coherence is mandatory.
- **Inside the cell, internals may diverge and be regenerated** (D6) — the AI navigates internal incoherence fine (E), so cosmetic uniformity there is not worth enforcing.
- **Coherence is enforced at the boundary**: fitness functions and the ratchet check the contract (no cycles across cells, stable entity shapes, layering), the self-model surfaces the sites, the steward judges the residue. The blast radius of incoherence is contained within a cell because the contract isolates it.

This reframes the method's *target* without discarding its mechanisms — it points them at the seams:
- prevent-by-plan / architect agent → **author the contract**;
- self-model (A) → **surface and register the contracts**;
- fitness functions + ratchet → **enforce coherence at the contract**;
- regeneration / disposable internals (D6) → **apply within the cell**;
- emergent-ratified canon (B) + convergence (C) → **settle the contract's shared shapes**.

## Honest caveats
- **A synthesis, not a measurement.** Each input is a small probe (n=8–12, Claude/Python); F draws their joint conclusion. The strong open frontier is *how disposable can internals really be at scale* — D6 showed regeneration converges only under a pinned contract, and the long-horizon, large-system version is untested (the same macro limit as everywhere).
- It does not claim internals never matter — performance, security, and shared-internal-state cut across cells and still need attention; F's claim is about *structural/representational* coherence, where the cost is at the seams.

## Verdict
The chain converges on a single architectural recommendation: **coherence at the contract, freedom within the cell.** Pin the interfaces and entity shapes (structure-spec, surfaced by the self-model, enforced by fitness functions and the ratchet); let the internals diverge and regenerate, because an AI maintainer handles internal incoherence and the real cost lives at the boundaries. This is the constructive close to the question E opened — *is coherence even the right target?* — answered precisely: yes, at the seams.

→ book: the closing chapter and Ch.5/Ch.7 — the architectural target is contract/interface coherence with disposable internals (cell / blast-radius), unifying the method's mechanisms by pointing them at the seams; co-positions cleanly with *Architecture as Code* (fitness functions enforce the contract) and the structure-spec (which *is* the contract). The disposable-internals-at-scale claim is the named open frontier.

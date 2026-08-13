# Reframe E — Does structural incoherence cost an *AI* maintainer?

**The premise under test:** the book assumes incoherence is costly. That is a *human-maintainer* intuition. This tests it on an AI maintainer directly — and the result challenges the premise in a specific, bounded, useful way.

**Result: at the tested scale, incoherence did NOT cost the AI maintainer. A cross-cutting change (thread a discount through create→total→receipt) succeeded 8/8 on a fragmented codebase — identical to 8/8 on the coherent one — including correctly patching the *second divergent site* (a receipt that computes its own total from a different shape) that a human would be most likely to miss. The cost of incoherence is therefore NOT uniform: it concentrates where incoherence (a) breaks interoperability or (b) exceeds what the agent can see at once — not in visible, non-breaking internal mess.**

## Design
Two versions of the same working pipeline, same behavioural oracle (baseline total 1300):
- **Coherent:** one `Order` schema; `order_receipt` calls `order_total`, so a discount applied once flows everywhere.
- **Incoherent:** three divergent `Order` shapes across `create`/`totals`/`receipts` + adapters; crucially `order_receipt` **computes its own total from its own shape**, so a consistent discount needs the fix applied in *two* separate places.
Task: add `discount_pct`; the total must drop 10% **and the receipt must show the same discounted total**. Graded: FULL = total and receipt both consistent; PARTIAL = total fixed but receipt still shows the undiscounted amount (the divergence bug). 8 trials per version.

## Results

| Version | Full success | Partial (divergence bug) | Error |
|---|---|---|---|
| Coherent | **8/8** | 0 | 0 |
| Incoherent | **8/8** | 0 | 0 |

In the incoherent version the agent threaded the discount through both `totals.order_total` *and* the receipt's separate total computation, every time — it recognised the second divergent site rather than missing it. Sample receipts: `Order o1 for c1: 1170 GBP`.

## What it means — the premise is partly wrong, in a bounded way
- **Visible, non-breaking structural incoherence does not cost the AI maintainer the way it costs a human.** A human is slowed and error-prone reconciling three `Order` shapes and is liable to miss the receipt's separate total; the AI, seeing the whole small codebase at once, reconciled them cleanly 8/8. This is a real, honest challenge to the founding intuition.
- **But the cost did not vanish — it relocated.** Two facets where incoherence *is* costly are established or implied:
  1. **Interoperability breakage** — the entity-coherence experiment showed divergent shapes that don't interoperate cause literal `KeyError`s; that is costly to *any* maintainer regardless of reader. The cost is in incoherence that **breaks contracts**, not incoherence that is merely untidy.
  2. **Beyond-context scale** — the predicted failure mode (miss the second divergent site) did *not* fire precisely because the whole fragmented codebase fit in the prompt. At scale, the agent cannot see that the receipt computes its own total, and would miss it. The cost is in incoherence the agent **cannot see at once** — the same context-window boundary as H1/H5.

So the cost of incoherence to an AI maintainer concentrates at **(a) contract/interoperability boundaries** and **(b) the limit of what it can hold in context** — *not* in visible, internal, non-breaking divergence.

## Honest caveats
- One task (a cross-cutting discount), one small fully-visible fixture, Claude/Python, n=8 — a clean directional result, not a population rate. The strong claim ("incoherence never costs the AI") is *not* supported; the bounded claim (visible non-breaking incoherence is navigated fine; cost lives at contracts and beyond-context scale) is.
- The decisive untested case is the beyond-context one: re-run with the divergent site *outside* the agent's window (a large codebase) and the divergence bug should reappear — that is the experiment that would confirm the boundary.

## Gate decision (routes the rest of the chain)
**Gate (ii) fires:** the cost concentrates at contract/interoperability boundaries and at scale, not in internal uniformity. Consequences for the plan:
- **The book's coherence target pivots** from "keep everything structurally uniform" toward **"keep contracts/interoperability coherent, and make the system visible at scale"** — and away from cosmetic internal uniformity for the AI's sake (the AI doesn't need it when it can see the code).
- **Step A (self-model) is rescoped:** its value is the *visibility* root — making the not-currently-visible (the divergent site beyond the window; the contract a module must honour) queryable on demand — and pinning **contracts/entities**, not enforcing internal cosmetic patterns.
- **Step F (cell / blast-radius: coherence at contracts, disposable internals) is elevated** — it is now directly supported: internals can diverge if the AI can see them and they don't break a contract; coherence must hold at the boundaries.

→ book: a genuinely perspective-widening beat for Ch.1/Ch.2 and the closing chapter — *coherence matters for the AI maintainer at contracts and at scale, not as cosmetic uniformity*; this sharpens the whole method's target and is honest about where the human intuition over-reaches. Pairs with entity-coherence (interop breakage is the costly facet) and H1/H5 (the context-window boundary).

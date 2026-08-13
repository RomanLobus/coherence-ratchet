# Reframe E-b — Does incoherence cost the AI maintainer *beyond its context window*?

**The confirmation E needed:** E showed incoherence is cheap when the whole fragmented codebase is visible. E-b hides the second divergent site (the receipt that computes its own total) — its existence and call are shown, its body is not — to test whether the cost reappears at scale.

**Result: the cost reappeared, but small — incoherent 7/8 full vs coherent 8/8; only 1/8 hit the divergence bug. The dominant behaviour was resourceful: with the divergent site out of view, the agents routed the change to a *shared upstream chokepoint* so both downstream computations inherited it without touching the hidden module. So the AI is more robust to incoherence than the human intuition predicts — even partial visibility doesn't doom it, provided a shared route exists.**

## Results (oracle run against the FULL codebase, incl. the hidden receipts.py)

| Version (receipts.py body hidden) | Full success | Divergence bug (receipt undiscounted) |
|---|---|---|
| Coherent | **8/8** | 0 |
| Incoherent | **7/8** | **1/8** |

7 of 8 incoherent trials edited only `pipeline.py`, applying the discount **upstream** — mutating each product's `price_pence` before both the totals adapter and the receipt adapter run — so the total path *and* the unseen receipt path both came out discounted. They engineered around the hidden divergent site rather than failing on it. One trial missed it (the divergence bug). Coherent never failed, because its design has no separate divergent site to miss.

## What it means — premise refined, not confirmed
- **The strong boundary hypothesis ("hide the divergent site → the AI misses it") is only weakly supported.** The bug appeared 1/8 (incoherent) vs 0/8 (coherent) — a real signal in the predicted direction, but small, and at n=8 close to noise. The AI mostly *solved around* the invisibility.
- **The AI is resourceful under partial visibility — if a shared route exists.** It found an upstream chokepoint (the order's product data feeds both adapters) and applied the change there, so the divergence downstream became irrelevant. That is a coherence-*preserving* move the agent invented without being told.
- **The fixture understates the cost.** The shared upstream data is exactly the escape hatch the agent used. Where divergent sites are *truly independent* (no common ancestor to route through), the change cannot be made in one place and the cost should be larger — that case is untested, and is the honest residual.

## Combined E + E-b verdict
Across full visibility (E: 8/8 = 8/8) and hidden-site visibility (E-b: 7/8 vs 8/8), **structural incoherence is substantially cheaper for an AI maintainer than the human-maintainer intuition assumes.** The residual cost concentrates in two places, not in untidy-but-navigable code:
1. **Hard interoperability/contract breaks** — divergent shapes that don't interoperate cause `KeyError`-class failures (entity-coherence), costly to any maintainer.
2. **Independent divergent sites beyond the context window** — when the change cannot be routed through a shared point *and* the agent cannot see all the sites. (E-b's agents escaped via a shared chokepoint; without one, the 1/8 would grow.)

Visible incoherence, and incoherence with a shared chokepoint, the AI handles fine.

## Gate decision (now solid enough to route Step A and the thesis)
**Gate (ii), refined:** the coherence target is **interoperability/contract coherence + visibility of the divergent sites** — not cosmetic internal uniformity. And this *strengthens the case for Step A*: the self-model's value is precisely to **surface the hidden divergent sites** (and the contracts), which is what removes both the 1/8 residual *and* the no-shared-chokepoint case — the agent no longer has to get lucky finding an upstream route, because the model shows it every site the change must touch. A is rescoped to: make the not-visible queryable (visibility root) and pin contracts/entities, not enforce internal patterns.

## Honest caveats
- One task, small fixtures, n=8, Claude/Python; 1/8 is a weak signal. The claims are bounded: *cheap when visible or chokepoint-routable; costly at hard interop breaks and at independent-sites-beyond-context.*
- The cleanest next confirmation (not run) would remove the shared upstream chokepoint so the change *must* touch the hidden site — that would size the true beyond-context cost. Logged as the honest follow-up.

→ book: Ch.1/Ch.2 and the closing chapter — the coherence the AI maintainer needs is at contracts and via visibility, and the AI is markedly more robust to navigable internal incoherence than humans (a genuinely perspective-widening, evidence-backed beat). Directly motivates Step A (the self-model as the visibility mechanism) and Step F (coherence at contracts, disposable internals). Pairs with entity-coherence (the hard-break facet) and H1/H5 (the context boundary).

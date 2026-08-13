# Reframe A — A derived, queryable self-model as the visibility mechanism

**Rescoped by the E/E-b gate:** the self-model's value is not enforcing internal uniformity (the AI navigates that fine) — it is **surfacing the divergent sites a cross-cutting change must touch**, especially the ones beyond the agent's window, and doing so without going stale. This tests both roots at once: visibility and staleness.

**Result: the derived self-model drove cross-cutting consistency from 1/8 (blind) to 8/8, by naming every site that computes the order total — and it stays fresh by construction (it auto-detected a newly-added total site with no manual edit). It can replace the rot-prone curated catalogue as the method's substrate, dissolving the R4/R10 staleness risk.**

## Setup
An order total is computed at **two independent, divergent sites** — `billing.invoice_total` (over `order["lines"]`, qty×price) and `analytics.revenue_for_order` (over `order["items"]`, count×cents). The maintenance task: apply a 10% discount to the order total *everywhere it is computed, consistently*. Two arms, n=8:
- **A0 (blind):** sees billing + pipeline + create; the analytics site's body is hidden.
- **A1 (self-model):** same, plus an **auto-derived self-model** (`selfmodel.py`, a deterministic AST pass) that reports the total-computation sites and the divergent line shapes — and, having named `analytics`, the agent is given its source (modelling a query that points there).
Graded by oracle: consistent = *both* sites discounted (1170).

## Results

| Arm | Consistent (both sites) | Divergence bug (billing only) |
|---|---|---|
| A0 — blind | **1/8** | **7/8** |
| A1 — self-model | **8/8** | 0/8 |

A0's 7 failures patched only `billing` and left `analytics` undiscounted; its 1 success happened to route through the `create` chokepoint. A1 edited *both* sites every trial, because the self-model named both.

**Freshness (the staleness root):** adding a third total site (`reporting.quarterly_revenue`) and re-running the deriver picked it up automatically — the model went from 2 sites to 3 with **no manual edit**. A curated catalogue would have stayed stale until someone added the entry (the exact R4/R10 failure mode).

## What it means
- **The self-model is the visibility mechanism the gate predicted the method needs.** Surfacing every divergent site took a cross-cutting change from 1/8 to 8/8 consistent. The agent does not need internal uniformity — it needs to be *told where the sites are*, which is precisely what a derived model provides.
- **It reduces the method's biggest standing risk.** The curated catalogue / layering-spec rots (R4) and its freshness is the steward's hardest duty (R10). A derived self-model is regenerable and bound to a source revision. Generation time, revision, tree hash, extractor version, and ruleset hash make stale use detectable; they do not make staleness impossible.
- **It unifies four artefacts into one.** Catalogue, design memory, architecture model, and entity registry were separate, each rot-prone; the self-model is their derived, queryable union — one substrate the gate matches against, the ratchet baselines, and the agent queries.

## Honest caveats
- **The fixture still had a visible chokepoint** (`create` materialises both shapes), so A0 *could* have succeeded via it — 1/8 did. A0's failures were "didn't look beyond billing," which the self-model fixed by naming all sites. **Answered, 12 August 2026:** the no-chokepoint follow-up was built and run at n=30 per arm (`no-chokepoint.md`), and the blind arm fails 30/30 with the escape route closed, while the self-model arm reaches both sites 30/30. The prediction this caveat made about itself holds.
- **A1 conflates "naming the site" with "giving access to it"** — the model named `analytics` and the agent then saw its source. That is faithful to how a query works (you find a site, then read it), but it bundles two effects; a purist split is untested.
- **The self-model here is pre-computed and surfaced, not a live tool the agent calls mid-task.** A real implementation needs the query as a tool, and its retrieval/extraction quality is the open engineering problem (H1's boundary). The deriver is also a heuristic AST pass — a production version needs a real extractor.
- Toy, n=8, Claude/Python.

## Gate decision (the second plan checkpoint — can replace the catalogue)
**Gate fires "replace":** the derived self-model delivers catalogue-level visibility (1/8→8/8) *and* stays fresh automatically (the demo). So it can **replace the curated catalogue as the method's substrate**, dissolving the R4/R10 staleness risk. Consequences for the chain:
- **B (emergent canon)** becomes "how the self-model *blesses* the canonical pattern" — ratify the modal entry the model derives, rather than hand-author it.
- **D (coherence price)** computes its score *against the self-model*.
- **C (convergence)** is tested as the decentralised alternative *to* the central self-model.
The book's core artefact shifts from a hand-curated catalogue to a derived, queryable self-model, with the steward *ratifying and judging* rather than *authoring and refreshing*.

→ book: the central observed artefact is derived rather than hand-maintained; it is regenerable, revision-bound, and rejected when its provenance no longer matches. A separate human-owned intent file carries authority. Engineering gaps remain retrieval quality at scale and the no-chokepoint confirmation.

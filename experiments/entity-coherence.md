# Experiment — Entity / data coherence (a facet beyond the dependency graph)

**Why:** all prior architecture work measured the *module dependency graph*. But "architecture coherence" also means the *domain model* stays consistent — the same entity (`Order`) shaped the same way across the system. This tests whether AI fragments the domain model, and whether the two-stage detector extends to that facet.

**Result: AI fragments the domain model severely — five independent agents produced five mutually *incompatible* `Order` schemas — and this is more consequential than function duplication, because divergent entity shapes break interoperability rather than merely bloating code. The detector caught it cleanly (5/5) and surfaced the precise breaks.**

## (a) Fragmentation — five Order-touching tasks, independent agents
Each agent (seeing only its own task) invented its own `Order` shape. **5 of 5 distinct schemas**, and the divergence is interoperability-breaking, not cosmetic:
- **Line items:** `items` (4 modules) vs `line_items` (module 4) — `order_total` would `KeyError` on an order built by `create_order`.
- **Date:** `created_at` (producer) vs `date` (receipt) vs `order_date` (CSV) — three names, none matching the producer.
- **Customer:** `customer_id` (most) vs `customer_name` (receipt) — the receipt module cannot render an order the creator produced.
- **Money:** plain `float`/`int` (creator) vs `Decimal` required by the validator — a freshly created order *fails its own validation*; and `total` semantics differ (pre-tax vs post-tax-and-shipping).
- **Missing fields:** the creator never sets `currency`, which the validator requires → created orders fail validation; the CSV exporter expects `subtotal`/`tax`/`shipping` the creator never emits → blank cells.

**Control:** one agent given all five tasks produced a **single shared schema** (`order_id, customer_id, items, currency, status`). So the fragmentation is the independent-agent / no-shared-model condition — the same root as function reinvention, one level up at the domain model.

## (b) Detection — can the two-stage detector catch it?
A multi-trial LLM detector, given only the modules' source, was asked to find entities represented inconsistently:

| | Result |
|---|---|
| Flagged `Order` as inconsistent | **5/5 trials** (variant_count 4–5) |
| Also flagged `Customer` (2 variants: id vs name) | 4/5 — genuinely fragmented, correct |
| Also flagged `LineItem` (3 variants: `product_id`/`sku`/`name`) | 3/5 — genuinely fragmented, correct |
| Spurious inconsistency on a coherent entity | none observed |

It did more than flag — it identified the **specific interoperability failures**: the `items`/`line_items` KeyError, created-orders failing validation, the receipt needing `customer_name` no producer sets, the float/Decimal type drift. That is exactly the steward-actionable output the method wants.

## What it means
- **Domain-model fragmentation is real, and arguably the highest-damage facet.** Function duplication bloats; divergent *entity* shapes **break the system** — modules cannot exchange data (`KeyError`, failed validation, unrenderable records). AI produces this readily because each agent, lacking a shared model, invents its own representation. This is coherence decay the dependency graph is completely blind to (the imports could be perfectly acyclic while `Order` means five different things).
- **The detector generalises to this facet.** The same two-stage idea — extract candidate data shapes, let an LLM cluster by domain concept and flag divergence — works at 5/5 recall with good precision and surfaces the concrete breaks. The method's detection machinery is not specific to functions or modules; it extends to the domain model.
- **"Architecture coherence" must include entity coherence.** The book's signal set should be: dependency structure *and* domain-model consistency (and, still untested, cross-cutting-concern and naming coherence). Measuring only the import graph would miss the damage that actually stops a system working.

## Honest caveats
- Toy: 5 tasks, one primary entity, Claude/Python, generated-clean code; the detector saw all five modules in one context (the same scale wall as H1/H5 — at many modules it needs sharding/an index).
- The fragmentation is the *no-shared-model* upper bound (independent agents). Real teams share *some* models; the contribution is the severity (incompatible, behaviour-breaking) and that detection catches it, not a population rate.
- Entity coherence has no cheap deterministic floor analogous to AST shingling — extracting "data shapes" across dataclasses/dicts/Pydantic/ORM models is itself non-trivial; here the LLM did both extraction and clustering. A production version needs a real shape-extractor feeding the semantic stage.

## Verdict
Entity/data coherence is a distinct, high-consequence facet of architecture coherence that the dependency-graph work missed entirely: independent AI agents fragmented one `Order` into five incompatible schemas that cannot interoperate, where a single coherent agent produced one — and the two-stage detector caught the fragmentation 5/5 and named the specific breaks. The method extends to this facet; the book should treat domain-model coherence as a first-class signal alongside dependency structure, and name the cheap-extractor and scale work as the engineering gap. This is the function→architecture→*facet* progression continuing: there are more axes of coherence, and this is the one most likely to break a system.

→ book: add domain-model coherence to Ch.6's signals (entity divergence, not just dependency cycles) and to the detector's remit (Ch.7); the structure-spec (Ch.3) should pin canonical entity shapes, not only module layout. Open facets still untested: cross-cutting-concern consistency, conceptual/naming coherence, runtime/distributed architecture. Detection-extractor and scale are the engineering gaps.

# Experiment #(mechanism) — Design-time architect agent

**Why:** the integrator (#2) fixes fragmentation *after* it happens (and can break behaviour); the declared architecture model (#5) prevents it but is *hand-authored*. A third option: an **architect agent** that, before any implementer writes, designs the shared contract (canonical entity schema + shared helpers) the implementers must conform to — automating the design-time model.

**Result: the architect agent collapsed domain-model fragmentation before it happened — free-form gave 5/5 distinct Order schemas (and one agent drifted the domain entirely to shipments); architect-first gave 4/5 identical to the architect's canonical schema. Planning the shared contract up front works, with the honest caveat that the plan is only as good as the architect agent.**

## Design
Five Order-touching tasks, two conditions:
- **Free-form:** five independent implementers (the fragmenting baseline).
- **Architect-first:** one architect agent designs the canonical `order_schema` + shared helpers, then the five implementers build against that plan.

## Results

| | Distinct Order schemas (5 variants) | Carry the canonical core | Notable |
|---|---|---|---|
| Free-form | **5/5** | **0/5** | one agent drifted to a `shipment_id/tier/account_type` domain; another emitted only `shipping_charge` |
| Architect-first | **2/5** (4 identical, 1 subset) | **4/5** | the 5th was `order_total`, using a compatible read-only subset `{order_id, items, total_cents}` |

The architect produced a sensible canonical schema (`order_id, customer_id, items, currency, status, total_cents [minor units, derived], created_at`) plus shared helpers (`new_order_id`, `utc_now_iso`, `line_subtotal_cents`, `from_cents`), and the implementers conformed — including using `total_cents` consistently and computing it via the shared helper rather than hand-setting it.

## What it means
- **Designing the contract up front prevents the fragmentation entirely** — not detect-and-fix (integrator), not detect-and-feedback (#1), but never-fragment. It is the entity-level analogue of the architecture-model conformance result (#5), achieved by an *agent* generating the shared schema autonomously rather than a human declaring it.
- **It completes a spectrum of consolidation/coherence mechanisms**, by *when* they act:
  - **Prevent-by-plan** (architect agent — design the contract before authoring),
  - **Prevent-by-surface** (catalogue/memory — show the existing system during authoring),
  - **Correct-in-loop** (#1 feedback — detect the collision on the agent's own output),
  - **Fix-after** (integrator #2 — consolidate post-hoc, behind a proof).
  The earlier the intervention, the cheaper: the architect agent never created the five incompatible schemas the integrator would later have to merge (and risk behaviour on).
- **It is the "act on the agent's output" insight inverted to design time** — instead of a second agent cleaning up after, a first agent sets the shape before. Same idea (a dedicated coherence role), opposite end of the lifecycle.

## Honest caveats
- **The plan is only as good as the architect agent.** n=1 plan here; it happened to produce a clean schema. A poor architect plan would propagate a poor schema to all implementers — the lever concentrates the risk in one design step (which is also why a human steward should review the architect's plan, exactly as for the catalogue).
- Implementers still adapt the schema to their task (the `order_total` subset) — benign here, but schema *subsetting/extension* is a residual divergence vector the model/ratchet must still watch.
- Toy (5 tasks, one entity), Claude/Python, single run — directional.

## Verdict
A design-time architect agent prevents domain-model fragmentation at the source: it took five incompatible Order schemas down to one canonical schema (4/5 identical) by designing the shared contract before implementers wrote. It is the earliest and cheapest point on the coherence-intervention spectrum (prevent-by-plan → prevent-by-surface → correct-in-loop → fix-after), and it automates the structure-spec/architecture-model that #5 had hand-declared — at the cost of concentrating design risk in one step that the steward should review. Combined with the integrator (#2) and feedback (#1), the method now has a coherence lever at every stage of the agent lifecycle.

→ book: Ch.3/Ch.7 — an architect agent that authors the structure-spec/canonical schema up front is the prevent-by-plan front of the spectrum; the four mechanisms (plan → surface → feedback → integrate) map to the change lifecycle, and the steward reviews the architect's plan as it reviews the catalogue. Caveat: plan quality concentrates risk; subsetting/extension still drifts.

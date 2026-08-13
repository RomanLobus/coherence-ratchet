# Experiment N3 — how often do independent agents agree on an entity's shape?

**Direction:** `entity-coherence.md` recorded five independent agents producing five mutually
incompatible order schemas where a single agent produced one. That is an existence result at the level
that matters: one ensemble, n=1. The book makes a distributional claim from it, so the measurement
should be distributional too.

## Setup

Each trial is one agent, alone, on the same task: write `build_order(customer_id, items)` returning a
dictionary carrying the customer, the line items and the total. Trials are grouped into ensembles of
five afterwards, which is equivalent to running ensembles directly because the agents are independent
by construction, and lets one dispatch of a hundred trials produce twenty ensembles.

    independent   the task alone. Nothing says what an order looks like here.
    grounded      the same task, plus a ratified Order contract naming the canonical field set.

The scorer reads the keys of the mapping `build_order` returns, by AST, following the value through a
literal, a `dict()` call, subscript assignment or `update`. One hundred trials per arm per family.

## Result

| family | arm | ensembles | mean distinct shapes per 5 | ensembles in full agreement | distinct shapes across 100 trials |
|---|---|---:|---:|---:|---:|
| `claude-haiku-4-5-20251001` | independent | 20 | **2.75** | 1/20 | 9 |
| `claude-haiku-4-5-20251001` | grounded | 20 | **1.00** | **20/20** | **1** |
| `gpt-5.4-2026-03-05` | independent | 20 | **1.60** | 9/20 | 3 |
| `gpt-5.4-2026-03-05` | grounded | 19 | **1.00** | **19/19** | **1** |

Ratified grounding collapses cross-agent divergence to a single shape in both families: 100 of 100
trials identical in one, 98 of 98 parsed in the other. The separation is far past the thirty-point
rule and in the same direction in both families.

The independent arm's divergence is the ordinary kind rather than the exotic kind. All nine shapes in
the `haiku` arm are combinations of the same three decisions:

    customer_id | customer      ×      items | line_items      ×      total | order_total | total_cents

    44x  customer_id | items      | total
    26x  customer_id | line_items | total
    17x  customer_id | line_items | order_total
     4x  customer    | line_items | order_total
     3x  customer_id | items      | order_total
     2x  customer    | line_items | total
     2x  customer    | items      | total
     1x  customer_id | line_items | total_cents
     1x  customer_id | items      | total_cents

Every pair of these breaks on a `KeyError` at the boundary between them, which is the failure the book
describes, and none of them is anybody's mistake.

## What it corrects

**The original's headline was the tail, not the typical case.** Five agents producing five distinct
schemas did not occur once in forty ensembles across two families. The `haiku` mean is 2.75 distinct
shapes per five agents and the `gpt-5.4` mean is 1.60. Divergence is real and it is smaller than the
anecdote. Any manuscript sentence implying that independent agents typically produce five
incompatible schemas from five attempts should be restated to the measured means, and
`entity-coherence.md` should be cited for the mechanism rather than the rate.

**Ratification does the work the book claims.** One shape, every trial, both families. This is the
cleanest positive result in the programme, and unlike the earlier grounding arms it is not at ceiling
in its control condition: the independent arm genuinely diverges, so the grounded arm has somewhere to
improve from.

**The two families differ in how much they diverge, and reporting them pooled would hide it.** The
frontier model converges harder on its own, 87 of 100 trials on one shape against 44 of 100. Its
independent arm still produced three incompatible shapes and only nine of twenty ensembles agreed, so
convergence is not agreement.

## A probe defect found and fixed before the result was recorded

The first run of this probe produced a 36 per cent parse rate on the independent arm and a mean of
4.06 distinct shapes, which would have overstated divergence considerably. Two causes, both mine.

The scorer collected every string key in the module rather than the keys of the returned order, so
incidental mappings counted as part of the entity's shape. And the task was worded so bare that the
model repeatedly reached for an HTTP client and "built" the order through an API call, which put
request envelopes in the key set and left the returned value untraceable. That measured task framing,
not entity divergence.

The task now states that the function is pure and standard-library only, the scorer follows the
returned value through the four ways an order gets assembled, and both arms parse at 100 per cent. The
figures above are from the corrected run. The first run's numbers are superseded and are not quoted
anywhere.

## Honest limits

- One hundred trials per arm per family, one entity, one task. Ensembles are formed by grouping
  independent trials, which is faithful to independence and is not the same as five agents working in
  one repository at one time.
- The grounded arm supplies the canonical field set directly in the prompt. That is the artefact the
  method produces, and it is a stronger intervention than a self-model an agent has to query.
- An order is an easy entity with strong shared priors. A domain concept with no obvious naming
  convention would likely diverge further in the independent arm, and the grounded arm has no room to
  improve on one shape.
- Two vendors is not a survey. The gap between the families here is itself a reason not to generalise
  a divergence rate across tiers or vendors.

## Reproduce

    python3 experiments/harness/dispatch.py --probe probe_entity_ensemble.py \
        --trials 100 --model claude-haiku-4-5-20251001 \
        --out experiments/data/runs/ensemble/2026-08-12b-haiku-4-5
    python3 probe_entity_ensemble.py --tally experiments/data/runs/ensemble/2026-08-12b-haiku-4-5

Raw responses and manifests are committed for both families. Scoring re-runs offline and needs no key.

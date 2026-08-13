# Experiment N2 — the cross-cutting change with no chokepoint to route through

**Direction:** `reframe-A-self-model.md` measured a derived self-model taking cross-cutting
consistency from 1/8 blind to 8/8, and named its own weakness in the caveats: the fixture kept a
`create` function that materialised both order shapes, so the blind arm could succeed by routing
through it, and one trial in eight did. Chapter 12 concedes that the truly independent case is argued
from that boundary and not directly measured. That undemonstrated case is the regime the book's claim
describes, so it is the one worth measuring.

## Setup

`_fixtures/nochokepoint/shop` computes the order total at two sites with no ancestor, no caller, and
no materialising function between them:

    shop/billing.py    invoice_total(order)        sums order["lines"]  as qty * price
    shop/analytics.py  revenue_for_order(order)    sums order["items"]  as count * cents

No module reads both keys, and neither file mentions the other's vocabulary. `shipping.py` also reads
`order["lines"]`, which makes the tree realistic without opening a path between the two totals;
`customers.py` reads neither. Both functions return 1300 on the fixture order, so a correct change
leaves both returning 1170 and the oracle is one number.

The task is to apply a ten percent discount to the order total everywhere it is computed,
consistently. Two arms, thirty trials each, run against two vendors (see the replication below):

- **blind** — sees billing, shipping and customers. The analytics site is not in context.
- **selfmodel** — the same, plus a derived self-model naming both total-computation sites, and the
  analytics source the model pointed at.

The oracle executes the returned modules against the fixture order. A site the response did not
return is treated as unchanged, which is what it is. Consistency requires both sites at 1170.

## Result — 0/30 blind, 30/30 with the self-model

| arm | n | consistent | divergence bug (billing only) | touched analytics |
|---|---:|---:|---:|---:|
| blind | 30 | **0/30** | **30/30** | 0/30 |
| selfmodel | 30 | **30/30** | 0/30 | 30/30 |

Wilson 95% intervals: blind consistency [0.00, 0.11]; self-model consistency [0.89, 1.00]. The
intervals do not touch.

**The prediction the original run made about itself holds.** Its blind arm scored 1/8 rather than 0/8
because of the chokepoint, and with the chokepoint removed the blind arm fails every time. Thirty
trials out of thirty patched `invoice_total`, returned it as the whole change, and left
`revenue_for_order` computing the undiscounted total. Not one of them went looking for a second site.

The self-model arm reached both sites in every trial. The arm still bundles naming a site with
granting access to it, which is faithful to how a query works and is the same bundling the original
run disclosed; a purist split remains untested.

## Replication across a second vendor

The same probe, unchanged, was dispatched to `gpt-5.4-2026-03-05`, a frontier tier from a different
vendor, at the same thirty trials per arm. Reported per family and never pooled.

| family | arm | n | consistent | divergence bug |
|---|---|---:|---:|---:|
| `claude-haiku-4-5-20251001` | blind | 30 | 0/30 | 30/30 |
| `claude-haiku-4-5-20251001` | selfmodel | 30 | **30/30** | 0/30 |
| `gpt-5.4-2026-03-05` | blind | 30 | 0/30 | 30/30 |
| `gpt-5.4-2026-03-05` | selfmodel | 30 | **30/30** | 0/30 |

The result is identical in both families, which matters most for the blind arm. A frontier model from
a different vendor, five months newer, failed the cross-cutting change in every one of thirty trials
in exactly the way the smaller model did: it patched the site it could see and left the site it could
not. The objection that a more capable model would find the second site is answered for these two
families at this sample, and the mechanism claim is about context rather than about a model.

The replication also retires a line in `open-directions.md`, which listed non-Claude replication under
work that was infeasible with the tooling available. It stopped being infeasible when the harness
gained a second transport.

## A measurement bug found and corrected, recorded because it changes a printed number

The first scoring of this run reported 29/30 for the self-model arm. The single failure was not a
model failure. The harness extracted only the *first* fenced code block from each response, so a
trial that returned two files in two blocks had its second file silently dropped, and the oracle
correctly scored the missing file as unchanged. The failure therefore looked like a model error while
being a harness error, which is the worst shape a measurement bug can take.

`extract_code` now joins every fenced block, `--rescore` re-extracts from the committed raw responses
before scoring, and the corrected figure is 30/30. Re-scoring `fullcontext-fragmentation`'s run under
the fixed extractor left all four of its conditions unchanged, so no other printed number moves.

The bug is recorded rather than quietly fixed because it is the case for keeping raw responses. The
error was invisible in the scores, discoverable only in the response, and repairable offline without
spending a further call.

## What it means

**The visibility claim survives its own hardest case.** The book's argument is that an agent does not
need a uniform system, it needs to be told where the sites are. The original run supported that with a
fixture that left an escape route. With the route closed, the blind arm's failure is total and the
self-model's success is total, and the claim rests on a measurement of the regime it actually
describes.

**The failure mode is silent by construction.** Every blind trial produced a change that is correct
where it looks and wrong where it does not, with no error, no test failure in the touched module, and
no signal at review beyond someone knowing that a second site exists. That is coherence debt being
created, in one commit, by an agent behaving reasonably.

## Honest limits

- Thirty trials per arm per family, two families, two dated snapshots, a four-module fixture. The
  separation is complete in both, so a larger n would tighten intervals without changing direction.
  Two vendors is not a survey of models.
- The self-model arm names the site *and* supplies its source. Naming alone, with retrieval left to
  the agent, is the untested purist split and the one a production implementation faces.
- The two sites diverge in field shape (`lines`/`qty`/`price` against `items`/`count`/`cents`), which
  is what makes them independent and also what makes them findable once named. Two sites that diverge
  less obviously would be a harder case for the deriver, not for the agent.
- The agents had no tools. An agent able to grep would plausibly find the second site in the blind
  arm, so this measures a harness without retrieval, which is the common condition and not the only
  one.

## Reproduce

    python3 experiments/harness/dispatch.py --probe probe_nochokepoint.py \
        --trials 30 --model claude-haiku-4-5-20251001 \
        --out experiments/data/runs/nochokepoint/2026-08-12-haiku-4-5
    python3 probe_nochokepoint.py --tally experiments/data/runs/nochokepoint/2026-08-12-haiku-4-5

Raw responses and the manifest are committed. Scoring re-runs offline and needs no API key.

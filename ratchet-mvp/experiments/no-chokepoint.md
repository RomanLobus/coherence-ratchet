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
run disclosed. The factorial below splits the two factors and supersedes this paragraph: the
split was tested on 22 August 2026, and access rather than naming is what this arm was measuring.

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

## The factorial, 22 August 2026 — the confound resolved, and the result reversed

The two arms above differ in two ways at once: the self-model arm receives the self-model *and* the
`analytics.py` source the model points at. The write-up disclosed the bundling and left the split
untested, and the manuscript then presented the self-model as the cause. This run tests the two factors
independently, all four cells, thirty trials per cell, on both families at their dated snapshots.

|  | self-model absent | self-model present |
|---|---|---|
| **analytics withheld** | `blind` | `named_only` |
| **analytics supplied** | `source_only` | `selfmodel` |

### Result

| arm | haiku consistent | gpt consistent | haiku both-discounted | haiku destructive |
|---|---:|---:|---:|---:|
| blind | **0/30** | **0/30** | 0/30 | 0/30 |
| named_only | **0/30** | **0/30** | 25/30 | **26/30** |
| source_only | **30/30** | **30/30** | 30/30 | 0/30 |
| selfmodel | **30/30** | **30/30** | 30/30 | 0/30 |

`claude-haiku-4-5-20251001` and `gpt-5.4-2026-03-05`, 30 trials per arm per family, every response and
a manifest committed under `data/runs/nochokepoint/2026-08-22-*`.

**Access is what the original number measured.** `source_only` reaches 30/30 on both families with no
self-model present at all. Where the second site is in the context window, the derived model adds
nothing this fixture can detect, so the 0/30 against 30/30 reported above is a measurement of source
access and not of grounding. Any claim that the derived model produced that separation is unsupported,
and the manuscript has been corrected.

**Naming without access never produced a correct change, on either family.** The two families fail it
differently, and the difference is the more useful half of the run. `gpt-5.4` returns 0/30 on
both-discounted: told that `shop/analytics.py` computes a total and given no way to read it, it patches
billing and stops. `haiku-4-5` returns 25/30 on both-discounted and **26/30 destructive**: it rebuilt
the module it had never read from the two lines of description, got the arithmetic right, and silently
dropped `order_bucket`, the sibling function the description did not mention. Every one of those
twenty-five "successes" deleted live code.

The task says "Change nothing else", so those trials are failures, and the corrected oracle records
them as such. Scoring only the returned number would have printed 25/30 as a win for naming.

### What this adds, rather than only what it removes

A named site the agent cannot reach is worse than an unnamed one. The blind arm patches one site and
leaves the other alone, which is a divergence a reviewer can find. The `named_only` arm, on the family
that complied, produced a plausible replacement file with a function missing, which is a regression a
reviewer has to notice the absence of. This is the fabrication hazard measured on this book's own
fixture: an agent asked to act acts, and a description is not a file. It corroborates, from a different
direction, the external finding that a missing fact produces wrong work rather than absent work
(Mohammadi et al., arXiv:2608.16630, 2026), and it is the sharpest available argument for a grounding
pack naming only what the agent can retrieve.

### Scorer corrected after the run, prompts unchanged

The preservation check was added to `score_code` after the responses were collected, so
`probe_sha256` moved while every `prompt_sha256` above stayed fixed. The persisted responses were
re-scored offline; no trial was re-billed and no prompt changed. The correction is recorded here rather
than folded in silently, because it turned 25 apparent successes into 25 failures.

## Honest limits

- Thirty trials per arm per family, two families, two dated snapshots, a four-module fixture. The
  separation is complete in both, so a larger n would tighten intervals without changing direction.
  Two vendors is not a survey of models.
- The self-model arm names the site *and* supplies its source. Naming alone was the untested split
  when this limit was written; the factorial tested it and found it worse than silence on one family
  (26/30 destructive). What remains untested is naming plus a retrieval tool the agent can call,
  which is the shape a production implementation would take.
- The two sites diverge in field shape (`lines`/`qty`/`price` against `items`/`count`/`cents`), which
  is what makes them independent and also what makes them findable once named. Two sites that diverge
  less obviously would be a harder case for the deriver, not for the agent.
- The agents had no tools. An agent able to grep would plausibly find the second site in the blind
  arm, so this measures a harness without retrieval, which is the common condition and not the only
  one.

## Reproduce

The four-cell factorial is the run the figures come from. The 2026-08-12 directories hold the
superseded two-arm run and are kept as the record of what was claimed before the split was tested.

    # re-derive every figure from the committed responses; no API key, no model call
    python3 experiments/harness/dispatch.py --probe probe_nochokepoint --rescore \
        experiments/data/runs/nochokepoint/2026-08-22-haiku-4-5
    python3 experiments/harness/dispatch.py --probe probe_nochokepoint --verify \
        experiments/data/runs/nochokepoint/2026-08-22-haiku-4-5

    # and to buy a fresh sweep against the vendor
    python3 experiments/harness/dispatch.py --probe probe_nochokepoint.py \
        --trials 30 --model claude-haiku-4-5-20251001 \
        --out experiments/data/runs/nochokepoint/<new-date>-haiku-4-5

Raw responses, the collection manifest and `rescore.json` are committed for both families.
`--verify` reports `scores_current` true: the committed scores were produced by the committed
scorer. It also reports `probe_changed` true, which is the honest record of the scorer correction
described below and not a failure of the run.

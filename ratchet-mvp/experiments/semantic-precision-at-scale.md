# Experiment H5 — Semantic detector: does precision hold at scale?

**Hypothesis (defends E2):** E2's zero false merges held on 10 clean, concept-separated functions. At larger size, with functions that share *partial* concerns, the LLM concept-clustering pass should over-merge — precision should drop.

**Result: it did not drop in the regime tested. On 56 functions with overlapping-concern stress, multi-trial consensus clustering scored precision 1.000 and recall 1.000 — no false merges, no missed groupings.** The honest force of the result is bounded by what the set was: 8 coarse, well-separated concepts of generated-clean code, with only mild concern-overlap. The result that *would* break it lives one regime further out, and converges with H1's boundary.

## Design
56 functions, names neutralised to `fn_001…` so clustering works from code, not labels:
- **8 concepts × 5 divergent implementations** (retry, paginate, to-cents, slugify, memoize, validate-email, debounce, running-average) = 40 functions;
- **8 overlapping-concern functions** — each a primary concept plus a secondary behaviour (a retry that also logs, a paginator that also validates bounds, a memoizer with TTL), labelled by primary concept — the precision stress;
- **8 unrelated singletons** (quicksort, fibonacci, hex-to-rgb, …) that must stay unclustered.

5 clustering trials; a pair counts as co-grouped only if ≥3/5 trials agree (consensus). Scored pairwise against ground truth.

## Results

| Metric | Value |
|---|---|
| Pairwise precision (co-grouped pairs that are truly same-concept) | **1.000** (TP=120, FP=0) |
| Pairwise recall (same-concept pairs that got co-grouped) | **1.000** (FN=0) |
| F1 | **1.000** |
| False merges at consensus | **none** |
| Singletons wrongly clustered | **none** |

Per-concept cohesion was 1.00 for seven of eight concepts and 0.93 for the eighth — one trial split a single overlapping function (a "retry that also logs") into its own group, which consensus then corrected. The overlapping-concern functions were otherwise attached to their correct primary concept every time.

## What it means
- **E2 was not a small-n artefact.** The clean separation held when the set grew 5× and gained overlapping-concern functions. The two-stage detector's semantic pass is reliable at moderate scale under consensus voting.
- **Consensus voting earns its place.** The one defection (0.93 cohesion) shows single-trial clustering is slightly noisy; the 3/5 rule absorbed it with no precision cost. This is the same multi-trial discipline the catalogue gate uses, vindicated again.
- **It converges with H1 on where the real limit is.** H1 found LLM retrieval robust until the catalogue exceeds the context window; H5 finds LLM clustering robust until — by the same logic — the function set exceeds what fits in one prompt, *and* until the concepts are fine-grained enough to be genuinely confusable. Both point to the identical unsolved regime: too many items to see at once, and distinctions too fine to separate. That is precisely the justification for the two-stage funnel — cheap structural shingling shards the space into candidate clusters, and the semantic pass runs *within* a shard, never over thousands of functions at once.

## Honest caveats (why 1.000 is not "solved")
- **Eight coarse, well-separated concepts.** Real codebases carry many near-but-distinct concepts (five flavours of validation; retry vs retry-with-circuit-breaker). Clustering eight obviously-different ideas is the easy case; the precision risk is fine-grained distinctions, which this set did not contain.
- **Generated-clean code.** Each function was generated to implement a named concept, so it is more canonical than organic divergent reimplementation. Messy real code is harder.
- **Mild overlap.** The overlapping-concern functions were primary-concept-dominant (a logging retry is still clearly a retry). A genuinely 50/50 function — sitting between two concepts — was not constructed, so the hardest precision case is untested.
- **56 functions fit in one prompt.** At thousands, the model cannot see them all; this says nothing about that regime except that sharding is required (the funnel).
- Claude-only, Python, 5 trials.

## Verdict
The semantic detector held precision and recall at 1.000 on 56 functions with mild overlapping-concern stress under consensus voting — strong evidence that E2's result scales past the toy case and that the two-stage detector is sound at moderate scale. It is not evidence that clustering is solved: the failure regime (fine-grained confusable concepts; sets too large for one context; genuinely ambiguous functions) was not reached, and the book should claim the measured result (reliable at moderate scale, well-separated concepts, with consensus) and name the untested regime as the open one — which is exactly where the structural pre-pass of the two-stage funnel does the load-bearing work.

→ book: Ch.6 + Appendix A — the semantic stage gets a measured precision/recall figure (1.000 at moderate scale, consensus voting) and an explicit boundary (fine-grained/large-set untested), and the two-stage funnel is justified as the way to stay inside the regime where the LLM is reliable. Pairs with H1: the same context-window boundary governs both retrieval and clustering, and real index/sharding infrastructure is the named requirement beyond it.

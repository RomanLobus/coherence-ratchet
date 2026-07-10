# Experiment R6 — Does the triage funnel produce a human-sized list at scale?

**Question:** On a large codebase the deterministic detector will surface many clusters. Does the catalogue gate shrink that to something a human steward can actually review?

## The funnel, measured

**Top of funnel (deterministic detector, SQLAlchemy `lib/sqlalchemy`):** 6,342 functions → **797 redundant clusters** (duplication ratio 0.37), computed in **47s**. Two immediate conclusions:
- **The raw detector is not human-sized at scale.** 797 clusters is far past what a steward can triage. The detector alone is insufficient — which is precisely why the catalogue gate and the ratchet's *delta* framing exist. (This is the honest case *for* the rest of the method, made with its own tool.)
- **Performance is the documented O(n²) limit.** 47s at 6,342 functions is tolerable for a one-off but confirms a real codebase needs LSH/MinHash bucketing, not the MVP's pairwise comparison. Stated as a known limit.

**Reduction (catalogue gate, 12-cluster sample, 4-pattern illustrative catalogue, 5 trials):** **6/12 cleared (clear rate 0.50)**, 6 surfaced for review. The clears were the recurring sanctioned families — `_init_dbapi_attributes` across three dialects → `dialect-init`; `coerce_compared_value` across types → `dialect-type-coercion`; `getter` / `init_class_attribute` → `orm-descriptor-method`; `prefix_with`/`suffix_with` and the default/onupdate pair → `symmetric-api-pair` — each 5/5. The surfaced six were coincidental or genuine pairs (e.g. `_replace_bindmarkers`/`replace_marker`, test-helper pairs), also 5/5. Voting was unanimous on every cluster — the robustness from R5 holds at scale.

## Why the residue is bounded (the load-bearing argument)

The 50% clear rate came from only four catalogue entries — and those entries each cleared *several* clusters, because sanctioned families **recur** across a large codebase (one `dialect-init` entry covers every dialect; one `coerce_compared_value` entry covers every type). So:

- **Human review load scales with the number of *distinct, unsanctioned divergent concepts*, not with lines of code.** As the catalogue is populated to cover a codebase's real sanctioned families, clear rate rises and the residue shrinks toward that distinct-concept count. The 797 is an artefact of an *empty* catalogue.
- **The ratchet delta shrinks it again.** In normal operation you do not review all clusters; you baseline the existing ones and only *new* divergence past a region's budget surfaces per change. Per-change steward load is therefore small and roughly constant, independent of codebase size.

## Honest caveats
- **Clear-rate, not safety, at scale.** This run measured funnel *reduction* against an illustrative catalogue I wrote; it used no ground-truth labels, so it does not re-establish "0 dangerous false-clears" at scale — that safety property rests on the three labelled repos (R5). A fully-labelled at-scale safety run needs SQLAlchemy domain ground truth and is future work.
- **Illustrative catalogue.** The four patterns are plausible SQLAlchemy sanctioned families, not a maintainer-validated catalogue; a real one would clear more.
- **Sample is size-2–4 clusters**, 12 of 797; not a random-uniform draw of all cluster sizes.
- **O(n²)** performance is a real limit for the MVP at scale.

## Verdict
At scale the raw detector floods (797 clusters); the catalogue gate plus the ratchet delta are what make the steward's list tractable, and the residue is bounded by *distinct divergent concepts*, not codebase size — supported by a 50% clear from only four catalogue entries where sanctioned families recur. → book Appendix C, Ch.7; performance limit → Appendix C / dead-ends.

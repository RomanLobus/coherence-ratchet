# Experiment R5 — Does the catalogue-matching gate generalise?

**Question:** The catalogue-matching gate worked on `requests`. Does it hold on other codebases, or was that a one-repo artefact?

**Result: it replicates cleanly across three independent codebases.** Catalogue-matching (objective "match a sanctioned pattern or NONE," 5 trials, conservative 4-of-5 quorum to clear) was run on `requests`, `boltons`, and now `flask`, each with its own hand-written catalogue and ground-truth labels.

| Codebase | Clusters | Correct disposition | Dangerous false-clears | Catalogue constrained the model? | Human list |
|---|---|---|---|---|---|
| requests | 8 | 8/8 | 0 | yes | 8 → 3 |
| boltons | 6 | 6/6 | **0 / 2** | yes (refused to invoke its vendoring convention) | 6 → 4 |
| flask | 7 | 7/7 | **0 / 2** | yes (refused to invoke outside Flask knowledge) | 7 → 4 |

**Zero dangerous false-clears across all three.** In every case the genuine cross-module duplicates and consolidation candidates (boltons' vendored OMD copies; flask's identical `_make_timedelta` and the render/stream-template quartet) were surfaced to a human, not cleared — and the sanctioned families (verb wrappers/shortcuts, dict mirrors, decorator/registration families, template-helper registration) matched their catalogued pattern.

## Why it holds

The catalogue flips the burden of proof. Asked to judge intent from its own priors, the model rationalises any familiar-looking duplication as deliberate (the two subjective framings failed — see `semantic-gate-on-requests.md`). Forced to point at a *specific* catalogued pattern or return NONE, and told to ignore outside knowledge, it surfaces what the catalogue does not bless — even when it plainly recognises the codebase. Flask is the sharpest case: the model knew these were Flask internals and still returned NONE for the uncatalogued `_make_timedelta` copy, citing only the catalogue.

## Honest limits (state these in the book)

- **Python only.** The detector is Python-AST-based; cross-language generalisation (JS/TS, Java) is untested and would need a tree-sitter front-end.
- **One model family.** Judges are Claude subagents; a second model family (GPT, Gemini) was not runnable here, so robustness to judge-model choice is **not** established. Judge-tier variation (haiku vs higher tiers) is also not yet run.
- **Small n per repo and author-built ground truth.** 6–8 clusters each, labelled by one person; the catalogues were written to reflect each codebase's genuinely sanctioned patterns, but they are not independently validated.
- **The result is for the *matching* regime only.** It says nothing about the gate judging intent (which fails) — only about objective matching against an explicit catalogue.

## Verdict
Within the tested envelope — Python, Claude judges, multi-trial, conservative quorum, explicit catalogue — the gate's safety property (never clear a genuine duplicate; clear the sanctioned ones; respect the catalogue over its own priors) **replicates across three codebases**. That is strong enough to present the mechanism as working *with the stated limits*, and to name cross-language and cross-model replication as the next validation. → book Appendix C, Ch.7.

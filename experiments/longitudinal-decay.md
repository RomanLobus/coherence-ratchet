# Experiment — Longitudinal divergence over git history (the decay curve)

**Goal (strengthen the central thesis):** the thesis's weakest claim is that AI authorship drives whole systems toward incoherence *over time* — unmeasured at the architecture level (R1). This builds the missing measurement: run the divergence metric across the full git history of mature libraries and read the curve. Tool: `ratchet-mvp/longitudinal.py` (samples ~24 commits across a repo's history, measures the library source only — excludes tests — at each).

**Result: the measurement works and produces a clean curve — but it is a *control*, not a test of the thesis, and as a control it shows the opposite of decay: well-maintained human projects hold or *reduce* divergence over their life, including through the AI era. The repos chosen contain almost no AI-authored code, so they cannot speak to the AI claim. This sharpens what the thesis still needs rather than confirming it.**

## The curves (divergence ratio = redundant functions / total, library source only)

| Repo | Span | Early | Mid | AI era (2022→) | Trend | AI-author trailers |
|---|---|---|---|---|---|---|
| requests | 2011–2026, 2654 commits | ~0.19 (2013) | 0.18 (2016) | 0.170 (2022) → **0.164 (2026)** | flat→down | **2** |
| flask | 2010–2026, 2267 commits | 0.43 (2014) | 0.30 (2017) | 0.249 (2022) → **0.264 (2026)** | down, slight late tick | **0** |
| boltons | 2013–2026, 1239 commits | 0.31 (2017) | 0.28 (2020) | 0.276 (2023) → **0.255 (2026)** | down | **0** |
| httpie | 2012–2024, 1637 commits | 0.03 (2021) | — | **0.075 (2022)** → 0.056 (2024) | up (one repo) | **0** |

(Early small-codebase readings are noisy — under ~50 functions a single cluster swings the ratio.)

## What it shows
- **No general upward decay curve.** Across four mature libraries over 12–15 years, divergence did not trend up. Three of four (requests, flask, boltons) are flat-to-declining, including through 2022–2026. Mature projects actively consolidate — flask fell from 0.43 to 0.24 over its life.
- **The one rise is confounded.** httpie's 2022 jump (0.03 → 0.075) coincides with the function count more than doubling (137 → 316) — a feature expansion/refactor, not gradual drift. It is the only signal in the thesis's predicted direction and it is not clean.
- **A human-maintained baseline, measured.** This is the contribution R3 said was missing, for the control condition: well-reviewed, human-maintained code holds divergence flat or reduces it over time. That is the line any AI-decay claim must be measured *against*.

## The decisive limitation: this is the control arm, not the treatment
The four repos carry **essentially no AI-authored commits** (requests has 2 agent co-author trailers in 2,654 commits; the others zero). Elite OSS libraries with heavy human review are precisely where coherence is *defended*, and where AI is barely present in merged code. So this measurement **cannot** test "AI drives decay" — it measures human-maintained projects, which is the baseline, not the phenomenon. Reading any AI conclusion into these curves would be dishonest.

## What this means for the thesis (impartial)
- It **does not strengthen** the macro claim — and it gently warns against it: left to careful human maintainers, divergence does not climb, so "decay over time" is not automatic; it is a property of *how* a system is maintained.
- It **does deliver** the human baseline (flat-to-declining), which the book can state as measured fact — useful, and honestly more than the field had.
- It **relocates the real test**: to support the AI claim, the metric must run on **AI-heavy codebases** (many agent-authored commits, or AI-generated projects) and be compared against this baseline. Finding such repos with enough history is the methodological crux — and the genuine next experiment. Until then, the book should frame AI's effect as *plausible and mechanism-supported (the visibility findings E1/E3/H4), not yet demonstrated at the whole-system level*, and present this baseline as the control half of a measurement it invites the field to complete.

## The treatment arm — searching for AI-heavy codebases (the harder half)

To test the AI claim rather than the control, I searched GitHub for repos with many agent co-author trailers (`Co-authored-by: Claude/Copilot`) and measured the Python ones. Three findings, all honest, none confirming the macro thesis:

1. **The population barely exists yet (as of June 2026).** AI-heavy repos surfaced by commit search are overwhelmingly *young* (every credible candidate's first commit is 2026-06 — weeks old), *small*, and *frequently not Python* (the most AI-dense, motioneso/Jarv1s at 838 commits / 1,349 AI trailers, has zero `.py` files). There is **no AI-heavy codebase with the multi-year history needed to measure a decay curve** against the human baseline. The macro over-time AI claim is currently **unmeasurable for lack of mature subjects** — not refuted, un-testable, because heavy autonomous authorship is too new to have aged.

2. **The one clean AI trajectory did not run away.** `qte77/agentic-job-offer-to-application-kit` — 149 commits, essentially all AI-authored, `src/ajoa_kit/`, 3 weeks old — moved from early noise (0.43 at 28 functions) to **~0.25 and held** (0.253 at 79 functions). No upward decay over its short life; it sits at the *high end of the human baseline*, the same ballpark as decades-old flask (0.26) and boltons (0.25). n=1, 3 weeks, 79 functions — far too small and young to generalise.

3. **Young AI-built divergence levels overlap the human baseline.** A handful of AI-heavy Python repos measured at current HEAD: crypto-trading-ai 0.08, pokerpal 0.12, ajoa-kit 0.25 (credible); preprint-bot 0.33 and OSMM-manager 0.50 (not trusted — the crude source-dir heuristic likely swept in tests/vendored code). Against the human baseline (httpie 0.06, requests 0.16, boltons 0.25, flask 0.26), the credible AI readings **fall inside the human range**. There is no early signal here that AI-built code is dramatically more divergent than human-built — though these are weeks-old snapshots, not trajectories, and the exclusions are inconsistent.

**Treatment-arm verdict:** the experiment that would confirm the macro thesis cannot be run today, because AI-heavy codebases old enough to show a decay curve do not yet exist; and the young AI repos that do exist sit within the human divergence range and show no runaway decay in their short lives. This is the most important honest result of the whole measurement: the over-time AI-decay claim is **not yet demonstrable**, and the early evidence does not lean toward it. The book must not assert it — it should lead with the proven visibility *mechanism* (E1/E3/H4) and frame the over-time effect as a measurement the field cannot complete until AI-authored systems mature, with this baseline + tooling ready to run when they do.

## Honest caveats
- Treatment-arm snapshots used a crude source-dir heuristic with inconsistent test/vendored exclusions — the current-level numbers are indicative, not precise. The human-baseline curves (library source, tests excluded, ~24 samples) are the rigorous part.
- The metric is the MVP's structural divergence (AST token-shingling); it captures one facet of coherence, not all of design quality.
- ~24 sampled commits per repo; early small-n readings are noisy; library source only (tests excluded) for comparability.
- Four repos, all Python, all elite OSS — a deliberately conservative, well-maintained sample. That is exactly why they read as a control.

## Verdict
The decay-curve measurement is built, reproducible (`scripts/longitudinal.py`), and honest. It produced a human-maintained baseline that is flat-to-declining over 12–15 years — the opposite of runaway decay — and, crucially, the chosen repos contain almost no AI-authored code, so they are the control, not the test. The thesis is neither confirmed nor refuted by this; it is sharpened: the over-time AI claim must be earned on AI-heavy codebases against this baseline, and until that exists the book should lead with the proven *mechanism* (agents fragment because they can't see the system) and treat the over-time macro effect as an open measurement it has now half-built.

→ book: Ch.1/Ch.2 + the empirical-contribution framing — present the human-maintained baseline as measured (flat-to-declining), state the AI treatment arm as the open measurement, and lead the causal story with the visibility mechanism rather than an unproven decay curve. Dead-end nuance logged: "mature codebases decay structurally over time by default" — not in this sample; careful maintenance holds or reduces divergence.

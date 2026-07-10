# Experiment — Per-commit Δ-divergence: does AI-authored history consolidate less?

**Hypothesis (tests the sharpened thesis):** decay = fragmentation − consolidation. The thesis says AI lowers the consolidation term — AI-authored commits should consolidate (reduce divergence) *less often* than human commits. Test it directly: per-commit Δ in the divergence ratio, AI-authored vs human, within and across repos.

**Result: null and confounded. The experiment did not confirm the claim — and the one AI-heavy repo consolidated frequently (76% of its divergence-moving commits *reduced* divergence). The clean test the thesis needs cannot be run on public repos, because every AI-heavy repo has a human in the loop supplying consolidation.**

## What was measured
Per-commit duplication-ratio Δ over each repo's history (library source, |Δ|>0.002 counted as "moving"):

| Repo | Window | Moving commits | Consolidating (↓) | Fragmenting (↑) | Consolidation fraction | Net drift |
|---|---|---|---|---|---|---|
| ajoa-kit (AI-heavy, 135/149 AI commits) | full 149 | 17 (all AI-authored) | **13** | 4 | **0.76** | +0.25 (born from 0) |
| requests (human) | last 60 | 0 | – | – | – | −0.002 (flat) |
| flask (human) | last 60 | 4 | 1 | 3 | 0.25 | +0.011 |
| boltons (human) | last 60 | 2 | 1 | 1 | 0.50 | −0.002 |

## Why it's null and confounded (stated plainly)
- **The AI-heavy repo consolidated, not fragmented.** 76% of ajoa-kit's divergence-moving commits *reduced* divergence; its net +0.25 is the artefact of a repo growing from an empty 0.0, not decay. This is the opposite of the predicted effect.
- **Because a human is curating it.** ajoa-kit's commits carry Claude co-author trailers, but a human author (the repo owner) decides what merges and plainly prompts cleanup. It is *AI-under-human-direction*, not autonomous AI. So it cannot isolate "what AI does to the consolidation term unaided" — and what it actually shows is that AI *with* a human curator consolidates fine.
- **The human comparators were at steady state.** Mature libraries in a recent 60-commit window barely move divergence at all (requests moved on 0 of 60). Their consolidation happened years earlier (the longitudinal curve caught flask's 0.43→0.24). A recent window is the wrong place to observe human consolidation events — a design weakness.
- **Life-stage mismatch.** Young, actively-built (ajoa) vs mature, frozen (requests/flask) is not an AI-vs-human contrast; it is early-vs-late, which dominates the per-commit signal.

## What it does and doesn't mean
- **It does not provide first-party evidence that AI lowers the consolidation term.** That claim, in the book, rests on the literature (Huang 2026: agents remove less code; Horikawa 2025: agents refactor locally not structurally), not on this experiment. This probe failed to add first-party support and should not be cited as if it did.
- **It mildly supports the book's *prescription* rather than its *problem*.** AI with a human curator and active shaping held coherence (ajoa settled ~0.25, consolidating 76% of moving commits). That is consistent with the thesis's *solution* — supply the consolidation discipline (here, a human steering) and coherence holds — even as it fails to demonstrate the *problem* (autonomous AI decaying).
- **The clean test remains unavailable.** Isolating AI's effect on the consolidation term needs autonomous AI authorship with no human consolidation, sustained long enough to integrate — which does not exist in public repos today (see `longitudinal-decay.md`: AI-heavy repos are weeks old and human-curated).

## Honest verdict
A null, confounded result. The per-commit differential neither confirmed nor cleanly tested "AI consolidates less," and the AI-heavy repo it could measure consolidated frequently under human curation. The sharpened thesis (decay = fragmentation − consolidation) stands on its logic, the measured human baseline, and the cross-sectional literature on AI's two terms — but **not** on this experiment. The book should keep the consolidation-term claim attributed to Huang/Horikawa, present the human baseline as the measured part, and treat "AI lowers consolidation in practice, unaided" as an open measurement alongside the macro decay curve — both blocked by the same fact: autonomous, aged, AI-authored systems do not yet exist to study.

→ book: do not cite this as evidence for the consolidation-term claim (literature carries it). Log as a dead-end/limit: "per-commit AI-vs-human differential" is confounded by the human-in-loop and life-stage; a clean version awaits autonomous AI codebases. The one forward-leaning note — AI-under-human-curation held coherence — belongs with the *method's* evidence (the steward/consolidation discipline works), not the problem's.

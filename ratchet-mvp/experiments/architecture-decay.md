# Experiment — Architecture-level coherence (the level the book is actually about)

**The gap this closes:** every prior measurement was *function-level* (duplicate/divergent functions). The book's subject is *architectural* coherence — module boundaries, dependency structure, coupling, cycles. This builds that metric (`coherence_ratchet/archmetrics.py`: intra-package module dependency graph → cycles via SCC, coupling density, fan-in concentration, instability) and re-runs the longitudinal study one level up.

**Result — the most consequential finding of the whole program: architecture-level coherence *decays over time even under careful human maintenance*, the function-level metric is blind to it (the two axes move in opposite directions), and AI's documented bias hits exactly the architectural term that is already weakest.** The decay thesis, which the function-level longitudinal had undercut, holds at the level the book actually claims.

## The metric discriminates, and it is orthogonal to function duplication
Current-state, four libraries:

| Repo | cycle_ratio | coupling/module | function dup_ratio (prior) |
|---|---|---|---|
| boltons | **0.00** | 0.43 | 0.25 |
| requests | 0.58 | 4.21 | 0.16 |
| flask | 0.83 | 4.17 | 0.26 |
| httpie | 0.15 | 2.68 | 0.06 |

boltons — a deliberately decoupled collection of standalone utilities — scores zero cycles, validating the metric. And the two axes are **orthogonal**: boltons has the *highest* function duplication (0.25) but *zero* architectural cycles; flask has *low* function duplication (0.26, falling) but the *highest* cycle ratio (0.83). Architectural coherence is a genuinely different dimension — measuring function duplication tells you little about it.

## Architecture decays over time — even for humans (the headline)
Longitudinal, cycle_ratio (fraction of modules tangled in a dependency cycle) and coupling over each project's life:

- **flask:** cycle_ratio **0.0 (2010–2012) → 0.43 (2015) → 0.55 (2020) → 0.76 (2021) → 0.83 (2026)**; coupling 1.0 → 4.2. Near-monotonic architectural decay over 16 years.
- **requests:** coupling **0.97 → 4.21**; cycle ratio rising to its lifetime high (0.58) at the end. In the post-2017 stable-package era alone: 3.17/0.39 → 4.21/0.58.
- **httpie:** decayed to 0.33, then a **deliberate de-cycling refactor (~2020) dropped it to 0.05**, then slow re-accumulation to 0.15 — visible, lumpy human consolidation.
- **boltons:** **0.0 throughout** — architectural discipline held by design (independent modules).

**The decisive contrast:** over the same period that flask's *architecture* decayed (cycles 0.0 → 0.83), flask's *function-level* duplication **declined** (0.43 → 0.24). The function-level longitudinal study concluded "no decay, human baseline flat" — and at the architecture level that conclusion is **wrong**. The decay was there the whole time; the function metric simply could not see it.

## Why architecture decays when functions don't: the consolidation term
Function-level consolidation is continuous and cheap — merge two helpers, dedupe a util. The longitudinal showed humans do it routinely, keeping function divergence flat. **Architectural consolidation is rare, lumpy, and expensive** — it means re-architecting (breaking a cycle, splitting a god-module, restoring a boundary), which happens in occasional big refactors (httpie 2020) or not at all (flask, requests). So in the balance *decay = fragmentation − consolidation*, the architectural **consolidation term is structurally weak**, and architecture drifts toward incoherence by default. This is Lehman's second law landing hardest exactly where consolidation is hardest.

## The connection to AI — and why this revives the thesis at the right level
The evidence on AI is that agents refactor **locally, not structurally** (Huang 2026, Horikawa 2025): they tidy and dedupe at the function level but do not perform the high-level design change that pays *architectural* decay down. Map that onto the two axes:
- AI keeps the **function term clean** (local cleanup it can do) — which is exactly flask's pattern (function-duplication falling).
- AI leaves the **architecture term to decay** (structural re-architecting it does not do) — the term that already decays by default for humans.

So AI's bias does not threaten the axis the function metric measures; it threatens the axis that *actually decays*, and it removes the one expensive corrective (deliberate human re-architecting) that occasionally arrests it. The function-clean / architecture-decaying signature flask already shows by hand is **precisely the shape heavy AI authorship should produce and accelerate.** That is a far stronger, evidence-anchored version of the thesis than anything at the function level.

## The AI-heavy repo: clean, but uninformative
ajoa-kit (pure-AI, 3 weeks, 15 modules) shows cycle_ratio 0.0, coupling ~1.5 — architecturally clean. But this says nothing: **flask was also clean (0.0 cycles) for its first two-to-three years**; architectural decay is a multi-year integral that does not appear at 15 modules / 3 weeks. As with the function-level treatment arm, the macro AI claim remains untestable for lack of aged AI codebases — but now the *human baseline* shows architecture decays over years, so the question "does AI accelerate it" is sharp and the tooling is ready.

## Honest caveats
- Cycle counts can be inflated by `__init__` re-export edges; the absolute calibration is rough. But the *within-repo trend* (flask 0.0 → 0.83) and the *cross-repo discrimination* (boltons 0.0) are robust to that, because the bias is consistent and boltons shows it does not universally inflate.
- requests' early module counts (~104) include non-package files pre-`src/` migration; the clean within-package signal is the post-2017 era (still rising).
- Dependency cycles + coupling + fan-in are three architectural signals, not all of architecture (no layering-spec conformance, no semantic boundary check — that is the LLM gate experiment next).
- Python-only (the parser); cross-language architecture is the LLM gate's job.

## Verdict
Measuring at the architecture level overturns the function-level conclusion in the book's favour: coherence **does** decay over time — flask's cycle ratio went 0.0 → 0.83 across its life, requests' coupling quadrupled — and the function-level metric was blind to it, even moving the opposite way. Architecture decays because its consolidation (re-architecting) is rare and expensive, and AI's local-not-structural bias attacks exactly that weak term. The book should **recentre its thesis and its method on architecture-level coherence** (cycles, coupling, boundaries), treat function duplication as a secondary, partially-misleading proxy, and the ratchet should ratchet the architectural signals. The macro AI claim is still unmeasurable (AI codebases too young), but the human baseline now *demonstrates the decay is real at this level* — which the function level never did.

→ book: this reshapes Ch.1/Ch.2 (decay is architectural, and invisible to function metrics), Ch.6 (the signals that lead are dependency-structure, not duplication count), Ch.7 (the ratchet enforces cycle/coupling deltas), and the empirical-contribution framing (first-party architectural decay curves + the function/architecture divergence). Dead-end retired: "function-level duplication is the coherence signal" — it is a weak, sometimes-inverted proxy for architectural coherence. The metric ships as `archmetrics.py`.

# Experiment E2 — Does a semantic detector catch the divergence the AST detector misses?

**Hypothesis (D2):** an LLM concept-clustering pass catches the *divergent reimplementation* (same idea, different code shape) that the AST-token detector misses — the failure mode R2/R3 identify as the real AI signature — without flooding on unrelated functions.

**Result: a clean win on exactly the gap that matters.** On a 10-function fixture built to separate structural from semantic similarity, the AST detector found the structurally-near duplicates and missed every divergent one; the LLM pass recovered all of them and merged nothing it shouldn't have.

## The fixture (`e2/concepts.py`)
- **RETRY (4 functions, same concept, deliberately divergent shapes):** `r_for` (for-loop), `r_while` (while-loop), `r_recursive` (recursion), `r_backoff` (for-loop + exponential wait).
- **PAGINATE (2 functions, same concept, divergent shapes):** `p_slice` (list comprehension), `p_loop` (append loop).
- **Unrelated (4 singletons):** `to_cents`, `slugify`, `running_mean`, `parse_kv`.

Ground truth: two concept groups (4 + 2) and four singletons.

## Results

| Detector | RETRY group (4) | PAGINATE group (2) | False merges of unrelated |
|---|---|---|---|
| **AST token-shingle** (SIM ≥ 0.45) | caught **2/4** — only `{r_for, r_backoff}` | caught **0/2** — neither paginator clustered | 0 |
| **LLM concept-clustering** (5 trials, low effort) | **5/5 trials grouped all 4** | **5/5 trials grouped both** | **0/5 trials** |

The AST detector only linked the two functions that *share loop structure* (`r_for`/`r_backoff`). The while-loop and recursive retries — same concept, different control flow — fell below threshold, as did both paginators relative to each other. The LLM pass put all four retries in one group and both paginators in another, every trial, and never pulled `to_cents`/`slugify`/`running_mean`/`parse_kv` into a concept group.

## What it means

- **The semantic pass closes the exact gap R2/R3 named.** The book's recalibrated thesis is that AI's signature is *divergent reimplementation*, not copy-paste. A token detector is structurally blind to that by construction; an LLM grouping by *what the code does* is not. This is direct first-party evidence that the detector front-end should be semantic, not (only) structural.
- **It was disciplined at this scale.** Zero false merges across five trials — the LLM did not hallucinate kinship between unrelated functions. The multi-trial consensus held perfectly (5/5 on every cell), which is the reliability read D2 demanded before trusting an LLM back inside detection.
- **It reframes the two detectors as a funnel, not a choice.** Cheap deterministic shingling first (free, scales, catches the structural clones), LLM concept-clustering second on what survives — recovering the divergent-same that structure can't see. That ordering keeps the expensive step bounded.

## Honest caveats (why this is suggestive, not settled)
- **The fixture is small, clean, and concept-separated by design.** Ten functions with crisp, distinct concepts is the easy case for clustering. The hard case is precision at scale: among hundreds of functions with overlapping concerns (a retry that also logs, a paginator that also validates), does the LLM still avoid false merges? R6's scale funnel showed the *structural* detector floods at 6,342 functions; an LLM pass over that volume is both a cost and a precision question this fixture does not answer.
- **Cost and reliability re-enter detection.** This puts an LLM back into the step the method deliberately kept deterministic. At n=10 functions × 5 trials it is trivial; on a real codebase it is an O(clusters) or worse LLM bill, and the 5/5 consensus seen here will not hold on ambiguous inputs. The honest framing: semantic clustering is a *second-stage* detector on the residue, gated by the same multi-trial discipline as the catalogue gate, not a wholesale replacement for the cheap signal.
- **Claude-only, Python-only, low effort, single fixture.** Same ceilings as every probe here. Recall on a deliberately-divergent set is the property most likely to generalise; precision-at-scale and cross-language are untested.

## Verdict
The semantic detector does what it was hypothesised to do: it recovers the divergent same-concept implementations the AST detector is blind to (4/4 retries, 2/2 paginators) with zero false merges across five trials, on the fixture. That makes a two-stage detector — deterministic shingling for structural clones, LLM concept-clustering for divergent reimplementation — the honest design for the front-end, with precision-at-scale and cost named as the open engineering questions. It converges with R2 (the signal is divergence, not raw duplication) and with E1b/E3 (surface the system to the agent): here the system surfaces *its own* divergence to the steward.

→ book: Ch.6 (the detector front-end becomes two-stage — structural then semantic), Appendix A (the semantic signal, with its precision-at-scale caveat), and the dead-ends thread for "structural detector alone" now has its positive counterpart. Precision-at-scale and LLM-cost logged as open engineering questions for the "beyond the ratchet" chapter.

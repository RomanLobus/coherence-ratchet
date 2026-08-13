# Experiment #3 + #4 — Task decomposition, and a consolidate-first norm

**Hypotheses:** (#3) how work is *sliced* drives fragmentation — many independent micro-tasks fragment more than one coherently-scoped task. (#4) a free, prompt-level "consolidate-first" norm reduces the additive bias.

**Result: both hold and both are cheap. Slicing the same work into five independent agents roughly *tripled* duplication versus one agent doing it whole (0.80 vs 0.27); and a consolidate-first norm cleaned the single agent's residual self-duplication to zero (0.27 → 0.00). The norm refines E1 rather than contradicting it.**

## Design
Five capabilities that share latent structure (two retrying fetchers, two cents converters, one paginator). Three arms, duplication measured locally with `measure()`:
- **A — sliced:** five independent agents, each seeing only its own task (the integrator experiment's `codeA`).
- **B-plain — coherent:** one agent given all five tasks at once.
- **B-norm — coherent + norm:** same, plus "keep the codebase consolidated; extract shared logic into one reusable helper; do not duplicate." 5 variants each of B.

## Results

| Arm | Duplication ratio |
|---|---|
| A — 5 sliced agents | **0.80** (4 of 5 functions redundant) |
| B-plain — 1 agent, all 5 | **0.27 mean** (3/5 variants 0.00, 2/5 variants 0.67) |
| B-norm — 1 agent + consolidate-first | **0.00** (5/5 variants) |

## What it shows
- **#3: decomposition is a first-order fragmentation lever.** Giving one agent the whole job cut duplication from 0.80 to 0.27 — roughly a 3× reduction — because the agent sees the shared structure and factors a single `_retry` and `_dollars_to_cents` across the sub-tasks, where five blind agents each reinvent them. This is a *process* lever leaders control directly: over-slicing work into isolated agent tasks manufactures the fragmentation. It is the same mechanism as the visibility finding (an agent reuses what it can see) applied to task scope — a broad task makes the siblings visible.
- **#4: a consolidate-first norm is a free top-up.** The single agent did *not* reliably self-consolidate (2 of 5 plain variants still inline-duplicated, 0.67). The norm took every variant to 0.00. So a one-line standing instruction removes the residual within-task duplication at no cost.
- **#4 refines E1, it does not contradict it.** E1 found a "reuse-or-justify" *wording* added nothing once a helper was already visible — because visibility alone secured reuse of an *existing* helper. #4 is a different act: the agent *extracting* a shared helper from its *own* multi-part output, which it does not always do by default. For that, the norm helps. The honest rule: norms don't move reuse-of-an-already-visible helper, but they do move self-consolidation of an agent's own output.

## Honest caveats
- **Both levers act only within one agent's context/session.** They reduce *within-task* fragmentation; they do nothing about the *cross-session / cross-agent* fragmentation (different agents, different days) that the longitudinal and E3 results identify as the real driver — that still needs design memory, the integrator (#2), or feedback (#1). #3/#4 are complementary, not a substitute.
- Toy 5-capability set, Claude/Python, 5 variants per arm — directional, not a rate.
- The single-agent arm's behaviour (`round(dollars*100)` in some variants vs Decimal in others) varies; the duplication metric is the measured quantity, not behaviour correctness here.

## Verdict
Decomposition and norms are the cheapest levers found, and both work within their scope: don't over-slice (a coherent task fragments ~3× less than isolated micro-tasks), and add a consolidate-first norm to mop up an agent's residual self-duplication (0.27 → 0.00). They refine the visibility thesis — a broad task and a standing norm both put more of the system in front of the agent at once — and they are free, but bounded to within-session work; the cross-session fragmentation still needs memory, the integrator, or feedback.

→ book: a short "how you scope agent work" section (Ch.5/Ch.7 — task scope as a coherence control) and the norm as a cheap default in the prevention layer (Ch.3), with the explicit boundary that both are within-session levers and the cross-session problem is handled elsewhere. Refines the E1 dead-end note: "norms don't help" → norms don't help *reuse-of-visible*, but do help *self-consolidation*.

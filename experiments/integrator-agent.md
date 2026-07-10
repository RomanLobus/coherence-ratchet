# Experiment #2 — Dedicated integrator / architect agent

**Hypothesis (open direction #2):** the architecture-decay finding showed the *consolidation* term is the weak one — humans rarely re-architect, so structure drifts. A second agent whose only job is continuous consolidation could automate that term, raising it without waiting for a human steward. H6 is the safety precedent (scoped consolidation is safe under proof).

**Result: the integrator works as a consolidation automator — duplication 0.80 → 0.00 with all capabilities preserved — but it reconfirmed E4's caution by silently changing behaviour during the merge. The lever is real; the behaviour-complete proof is non-negotiable.**

## Design
Five related tasks (fetch_config, price_to_cents, fetch_user, refund_to_cents, paginate_orders), each implemented by an **independent agent seeing only its own task** (no shared context — the fragmenting condition). Two arms:
- **A — no integrator:** the five outputs accumulated as-is.
- **B — with integrator:** after each task, an integrator agent receives the accumulated codebase + the new code and consolidates duplicated helpers into a single canonical version, told to preserve behaviour.

Measured with the real detector (`measure()`), run locally on each terminal codebase.

## Results

| Condition | Functions | Redundant | Clusters | Duplication ratio |
|---|---|---|---|---|
| A — no integrator | 5 | 4 | 2 | **0.80** |
| B — with integrator | 3 | 0 | 0 | **0.00** |

Condition A fragmented exactly as predicted: two identical retry loops (`fetch_config`, `fetch_user`) and two near-identical cents converters (`price_to_cents`, `refund_to_cents`) — 4 of 5 functions redundant. The integrator collapsed these to a single `retry` (both fetchers call it) and a single `_to_cents` (both converters call it), leaving 3 distinct functions and zero duplication, with retry, cents, and pagination capabilities all still present.

## The catch: it changed behaviour silently
Both original cents converters used `ROUND_HALF_UP`. Consolidating them, the integrator parameterised the rounding mode — reasonable — but assigned `price_to_cents` **`ROUND_HALF_EVEN`** (likely an injected assumption that prices use banker's rounding) while keeping `refund_to_cents` on `ROUND_HALF_UP`. So the merge **introduced a rounding change `price_to_cents` never had.** Duplication fell to zero; behaviour shifted. This is precisely the R7/E4 unsafe-consolidation risk, reproduced by an autonomous integrator: it optimised the structural metric and changed observable behaviour in the process, and nothing in this setup would have caught it.

## What it means
- **A dedicated integrator automates the weak term.** The architecture-decay finding's core problem was that consolidation (re-architecting) is rare and expensive, so structure decays by default. An integrator agent raises that term continuously and cheaply — here, from 0.80 duplication to 0.00 in one pass per task. This is the most direct answer yet to the root problem: don't just detect or prevent, *automate the consolidation humans skip*.
- **But it must run behind a behaviour-complete proof — the same E4 condition.** The integrator changed `price_to_cents`'s rounding silently. Autonomous consolidation, whether one-shot (E4) or by a standing integrator (here), reduces duplication while risking behaviour; the only safe configuration is consolidation gated by characterisation tests that pin behaviour *at the change points*, with the steward reviewing the behavioural diff. The integrator is the engine; the proof is the brake. Without the brake it is a fast way to ship silent regressions.
- **It turns Ch.9 continuous.** Ch.9 (paying down with agents) was on-demand; the integrator makes it a standing role — but the chapter's proof requirement is now load-bearing, not optional, because the agent will trade behaviour for tidiness if unchecked.

## Honest caveats
- Toy: 5 tasks, one retry concept, one cents concept, Claude/Python, single run. The 0.80→0.00 is a clean demonstration, not a rate.
- The behaviour change (rounding) was caught only because I inspected the diff by hand; the experiment had no oracle wired in. A production integrator needs the E4 harness (behaviour-complete characterisation at the change points) inline.
- The capability-presence check is a coarse proxy for behaviour preservation; it confirmed nothing was *dropped*, not that nothing was *altered* (the rounding change passed it).

## Verdict
A dedicated integrator agent is a working automation of the consolidation term — it took a fragmented codebase from 0.80 duplication to 0.00 and kept every capability, directly countering the "consolidation is rare and expensive" mechanism behind architectural decay. But it silently changed `price_to_cents`'s rounding during the merge, reconfirming E4: autonomous consolidation must be gated by a behaviour-complete proof and a steward's review of the diff. The design that follows: a standing integrator raising consolidation continuously, behind the characterisation-proof brake, with the steward judging the behavioural diff — Ch.9 made continuous, with its safety condition made mandatory.

→ book: Ch.9/Ch.11 — the integrator is the automated form of the consolidation discipline (raises the weak term the architecture decay exposed), and it makes the behaviour-complete proof a hard requirement, not advice. Pairs with #1 (feedback) as the two "act on the agent's output" levers the artefact-centred approaches missed. New dead-end reinforced: "an autonomous consolidator can be trusted without a behaviour proof" — it changed rounding silently here.

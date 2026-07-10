# Reframe D — Coherence as the agent's price (vs surfacing, vs feedback)

**Question:** agents optimise "task done + tests pass"; coherence is invisible to them. Does making a coherence *cost* (computed against the self-model/ratified canon) a visible objective at authoring reduce fragmentation **beyond plain surfacing** — and without causing inappropriate *force-fitting*?

**Result: a modest, honest yes. In a fuzzy-fit case the explicit coherence price nudged true reuse of the canonical helper from 4/10 (surfacing only) to 6/10, and backoff logic was retained in every case (no force-fit that crippled the requirement). But the effect is small, the fixture imperfect, and feedback-after (#1, 0→10/10) and surfacing (E1) remain the stronger levers. Incentive-shaping is a minor complement, not a dominant mechanism.**

## Setup
Canonical helper: a no-delay `retry(op, attempts)`. Task: `fetch_with_backoff` — retry with *exponential backoff* (which the canonical helper does not provide, so it only *partially* fits). Three arms, n=10:
- **plain** (no helper shown), **surfaced** (helper shown, E1-style), **priced** (helper shown + a coherence-budget instruction: a new divergent variant costs coherence, reuse/extend costs nothing).

## Results (true reuse = `retry` *called inside* `fetch_with_backoff`, not merely pasted)

| Arm | True reuse | Pasted-but-unused | Fresh own loop | Backoff logic present |
|---|---|---|---|---|
| plain | **0/10** | 0 | 10/10 | 10/10 |
| surfaced | **4/10** | 5/10 | 1/10 | 10/10 |
| priced | **6/10** | 2/10 | 2/10 | 10/10 |

The coherence price lifted true reuse 4→6/10 over surfacing, and every arm kept the backoff requirement (10/10) — so the price did **not** backfire into force-fitting (no agent crippled backoff just to reuse the helper).

## What it means
- **Incentive-shaping is a real but small lever.** Telling the agent coherence has a cost nudged it toward composing with the existing helper rather than rolling a fresh variant (4→6/10), on top of surfacing. It is a *complement* to prevention, not a replacement.
- **It did not cause force-fit.** The worry with pricing coherence is that the agent crams a poorly-fitting helper in to dodge the cost; that did not happen — backoff was preserved in all 10 priced trials. So the price is at least *safe* here.
- **The dominant prevention levers remain surfacing and feedback.** E1 showed surfacing flips reuse when the helper fits; #1 (in-loop feedback) drove reuse 0→10/10 by detecting the collision after. The coherence price adds a modest authoring-time nudge in the *fuzzy* middle where the helper only partly fits.

## Honest caveats
- **The fixture was imperfect:** a no-delay `retry` cannot cleanly *extend* into exponential backoff, so "reuse" here is a debatable composition (wrapping a no-delay helper to get backoff is awkward), and the correct answer for some agents was legitimately to write fresh. A cleaner fuzzy-fit fixture (helper does 80%, task needs a small genuine addition) would measure the nudge better.
- **Classifier bug caught and corrected:** the first pass counted `def retry(` as a call; the corrected count (call *inside* `fetch_with_backoff`) gives the 4→6 figures above. The *correctness* of the reuse-compositions (does the wrapped result actually back off and re-raise) is asserted from the backoff-logic regex, not executed — a residual uncertainty.
- n=10, Claude/Python, one task.

## Gate decision
**Adopt the coherence price as a minor complement, not a core lever.** Prevention is: surface the canonical pattern (E1) and feed back collisions (#1) as the primary mechanisms; the coherence-cost framing adds a small authoring-time nudge in the fuzzy middle, and is safe (no force-fit observed). For the chain: this refines the prevention layer; it does not change the substrate (the self-model, A) or the canon (B).

→ book: Ch.3/Ch.7 prevention layer — the coherence price is a light incentive nudge layered on surfacing and feedback (the stronger levers), shown not to backfire into force-fitting; modest effect, imperfect fixture, so claimed small. Logged follow-up: a clean fuzzy-fit fixture to size the nudge properly.

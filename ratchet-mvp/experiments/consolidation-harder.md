# Experiment H6 — Autonomous consolidation under harder fixtures

**Hypothesis (defends E4):** E4's 20/20 safe rate was an upper bound — small legible functions and a target helper expressive enough to represent every variant. Two harder cases should break it: a site whose behaviour the canonical helper *cannot* represent (a per-attempt metric — the safe move is to leave it), and a site whose behaviour depends on context outside the obvious arithmetic (a module-level flag).

**Result: it did not break at this difficulty. Agents recognised both traps from the code and stayed safe in 20/20 trials (documented + comment-stripped) — but the fixture did not reach the genuinely hard case (behaviour determined entirely outside the function), so this strengthens E4's conditions rather than finding their breaking point.**

Setup: a module with four retry sites onto a canonical `retry(op, attempts, exc, sleep)` that has **no per-attempt hook**. Site A (3 tries) and B (4 tries) are safe to consolidate. Site C (`fetch_metered`) increments a metric on each failed attempt — unrepresentable by `retry`. Site D (`fetch_flagged`) reads a module-level `AGGRESSIVE` flag for its attempt count. The characterisation suite is incomplete (does not test the metric or the flag); a behaviour-complete oracle does. A naive force-consolidation passes char but fails the oracle on both traps (verified). n=10, run twice: with guiding comments and with them stripped.

## Results

| | Oracle pass (all behaviour preserved) | Metric (C) preserved | Flag (D) preserved | Silent breakage |
|---|---|---|---|---|
| Documented (comments explain the traps) | **10/10** | 10/10 | 10/10 | 0/10 |
| Stripped (traps only in the code) | **10/10** | 10/10 | 10/10 | 0/10 |

How they handled the non-expressive site C differed by run: with comments, 7/10 consolidated it "carefully" (extending or guarding) and 3/10 left it inline; with comments stripped, 7/10 **left it inline** and 3/10 consolidated safely — either way the metric survived 10/10. Site D was consolidated onto `retry` in nearly every trial, always by reading the flag **at call time** (`attempts=6 if AGGRESSIVE else 3`), never by hardcoding — preserving the dynamic dependence 10/10.

## What it means
- **Agents respected E4's two conditions without being told.** "Leave the divergence when the abstraction can't preserve it" and "preserve context-dependent behaviour" both held when the traps were visible only in the code. The safe rate did not degrade from E4's clean fixture to this harder one.
- **The safety came from reading, again.** As in E4, the incomplete characterisation suite would have passed a naive consolidation; the agents avoided that by reading the metric side-effect in the `except` block and the flag read in the body. The behaviour-complete oracle, not the char suite, is what *verifies* it — the char suite alone would not have caught a failure.
- **This is consistent with H1 and H5.** A third attempt to find a breaking point at cheaply-constructable difficulty, and a third time the agent held up. The pattern across the hardening round: agents are more robust than the caveats feared *in the regime that fits in front of them and is legible*; the genuine limits sit further out than these probes reach.

## Honest caveats (why this is not "consolidation is always safe")
- **The non-expressiveness was legible from the helper signature.** `retry`'s docstring and parameter list visibly lack a per-attempt hook, so "this can't be expressed" was readable. A subtler unrepresentable behaviour (e.g. an ordering or exception-chaining nuance the helper *appears* to support but doesn't) would be a harder test.
- **The "context" was still local.** Site D's flag is a module global *read inside the function* — visible when reading the function body. The genuinely hard case the plan envisioned — behaviour determined entirely *outside* the function (a caller's surrounding `try/except`, an attempt count passed in from elsewhere, a monkeypatch) — was not constructed, and reading the function alone would not reveal it. So "context-dependent" here is the easy form of context-dependence.
- n=10 per run, Claude, Python, four-site fixture. The 20/20 is on this difficulty, not a general safety guarantee.

## Verdict
Scoped consolidation stayed safe (20/20) when one site was unrepresentable by the helper and another depended on a module flag — agents left or safely extended the non-expressive site and preserved the flag dependence at call time, with zero silent breakage, even with the explanatory comments removed. This strengthens E4's claim and its two conditions rather than bounding them. The honest limit is that the truly hard case — behaviour invisible when reading the function in isolation — was not reached; that, plus subtler unrepresentability, is where consolidation safety is still genuinely open. The standing requirement holds regardless: verify with a behaviour-complete oracle, because the pre-existing characterisation suite would have waved a naive consolidation through.

→ book: Ch.9 — agents respect "leave the non-expressible divergence" and "preserve context" conditions even unprompted at this difficulty; pair with E4's headline. The open limit (externally-determined behaviour, subtle unrepresentability) joins the future-work list. Reinforces, with H1/H5, the round's meta-finding: the LLM is reliable where the relevant facts are legible and in front of it; the unsolved cases are the illegible and the out-of-context ones.

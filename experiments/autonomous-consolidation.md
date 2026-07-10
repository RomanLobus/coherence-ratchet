# Experiment E4 — Autonomous consolidation under proof

**Hypothesis (D4):** R7 found refactoring ROI unproven and free-form refactoring risky (~7% behaviour-breaking; characterisation tests caught only 4/22 of the misses). But if consolidation is *scoped* (reduce these N variants to one named helper), *cheap*, and *proof-gated*, the economics and the safety profile may flip — the steward supervises rather than does.

**Result: scoped, proof-gated consolidation was safe in 20/20 trials — far better than free-form. But the safety came from the agent's care, not from the test net, and it rests on three conditions the book must state.**

## Design
A decayed module: four functions (`fetch_config`, `fetch_user`, `fetch_invoice`, `fetch_report`) each grew its own inline retry loop, with **subtle behavioural differences** a naive "just call `retry()`" pass would silently break:
- `fetch_user` runs **4** total tries (a `while tries <= 3` off-by-one), not 3.
- `fetch_invoice` catches **only `TransientError`** — a `ValueError` must propagate immediately, not be retried.
- `fetch_report` sleeps between tries (timing).

A canonical `retry(op, attempts, exc, sleep)` helper already exists, **expressive enough to represent every variant**. Two test suites: a **characterisation suite** (5 tests, happy-path + basic retry — deliberately *incomplete*, like real char tests) and a behaviour-complete **oracle** (pins exact try-counts and exception selectivity). Agents saw only the characterisation suite.

Ten agents per condition were asked to consolidate the four functions onto `retry` and keep the characterisation tests green. Each result was scored against both suites. Two conditions:
- **E4 (documented):** each site carried a comment naming its quirk ("total 4 tries… DIFFERENT attempt count"; "catches ONLY TransientError").
- **E4b (code-only control):** comments stripped — the divergence lived only in the code.

## Results

| Condition | Consolidated (4/4) | Char tests pass | **Behaviour preserved (oracle)** | **Silent breakage** (char green, oracle red) |
|---|---|---|---|---|
| E4 — documented | 10/10 | 10/10 | **10/10** | **0/10** |
| E4b — code only | 10/10 | 10/10 | **10/10** | **0/10** |

Every agent in both conditions consolidated all four sites and preserved every subtle difference — including reasoning the off-by-one straight out of the code in the control ("`while tries <= 3` from 0 is 4 total tries, so `attempts=4`"). Compare R7's free-form refactoring: ~7% behaviour-breaking.

## The uncomfortable finding: the test net is porous; the agent's care was the safety
A deliberately-naive consolidation (map all four to `retry(loader, 3, Exception)`) **passes all five characterisation tests** while breaking two behaviours — `fetch_user` silently drops to 3 tries, `fetch_invoice` silently starts retrying `ValueError`s. The characterisation suite the agents were given would have waved that straight through. So the 0/20 silent-breakage rate was **not** produced by the proof harness catching mistakes — no agent made one. It was produced by the model reading carefully. That is exactly R7's warning (tests caught only 4/22) reproduced: an incomplete characterisation suite gives false confidence, and the safety here depended on diligence that is not guaranteed at scale.

## What it means
- **Scoped reduce-to-canonical is a genuinely different task from free-form refactoring.** "Replace these four loops with this named helper, keep tests green" is bounded, legible, and verifiable. R7's risk figure is about open-ended restructuring; it should not be carried over to scoped consolidation. The economics R7 questioned (is refactoring worth it?) are also more favourable here: the change is small, mechanical, and supervised.
- **It works only when the canonical helper can express every variant.** All four divergences (attempt count, exception filter, sleep) were representable as `retry` parameters, so consolidation never had to *choose between* duplication and behaviour change. Had the helper been unable to express "catch only `TransientError`", the safe move would have been *not to consolidate* — and an agent told to consolidate might have changed behaviour instead. The book must state this: consolidate onto an abstraction expressive enough to preserve behaviour, or leave the divergence (this is the entropy budget's "leave bounded decay unfixed").
- **The proof must be behaviour-complete, not just the existing tests.** Since char-passing ≠ behaviour-preserved (demonstrated), proof-gated autonomous consolidation needs a behaviour-pinning step the agent does not author for itself — characterisation tests generated against the *current* behaviour at the exact points being changed (try-counts, exception types), or a human steward reviewing the behavioural diff. Trusting the pre-existing suite is the trap.

## Honest caveats
- **Small, legible fixture; one concept.** Four short functions with crisp divergences. Real consolidations bury behaviour across call sites, rely on a caller's surrounding `try/except`, or entangle state — harder to read and harder to preserve. The clean 20/20 is an upper bound.
- **Claude-only, n=10 per condition, Python, retry concept.** Suggestive, not a population rate. The honest sequel is a harder fixture (behaviour that depends on context outside the function) and a larger n.
- **No measurement of the residual at scale.** R6 showed the detector floods at 6,342 functions; this says nothing about consolidating hundreds of clusters, only that one cluster of four consolidates safely.

## Verdict
Autonomous consolidation, *scoped to reduce-to-a-named-helper and proof-gated*, was safe across 20/20 trials and preserved subtle behaviour the agents had to infer from code — a different and far better safety profile than R7's free-form ~7%. The two conditions the result depends on are clear: the canonical abstraction must be expressive enough to preserve every variant (else leave the divergence), and the proof must pin *current behaviour* at the change points, because the pre-existing characterisation suite is porous and the safety otherwise rests on model diligence alone. This turns Ch.9 from aspiration into a measured, conditional claim: agents can pay down this debt under supervision, and here is exactly what the supervision must check.

→ book: Ch.9 (paying down with agents — scoped, proof-gated, expressive-target; the steward reviews the behavioural diff, not the test pass); the entropy budget (Ch.5 — "consolidate only onto an abstraction that preserves behaviour, else leave it"); and the dead-ends thread keeps "free-form agent refactor without proof" (R7's 4-of-22) as the rejected alternative, now paired with the safe scoped form. The porous-char-suite finding reinforces Ch.6's behaviour-pinning requirement.

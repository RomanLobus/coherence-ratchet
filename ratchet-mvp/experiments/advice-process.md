# Experiment — Architecture Advice Process for a consolidation decision

> **RETIRED, 12 August 2026.** Not re-run at higher n: the design cannot ask the question,
> because a language model standing in for a person has neither the bounded working memory nor
> the accountability the claim turns on. Collected in Appendix C.8b, 'the two proxies that could
> not answer the question'. The underlying claims stay OPEN_HYPOTHESIS and need participants.

**Direction:** P12 (operationalises B3, Harmel-Law's *Facilitating Software Architecture*). The book's
steward is a (single) supervisor; the advice process is a decentralised alternative — anyone may decide,
provided they seek advice from those affected and those with expertise; the decider is accountable, the
advisors are not. This probe compares the two on a consolidation decision with a **hidden cross-module
constraint conflict**: `checkout.validate_order` and `admin.validate_order` look like near-duplicates,
but checkout *must* enforce a credit limit while admin *must* bypass it and require an `audit_reason`.
A naive merge breaks one workflow; the correct call is not-naive (leave, or conditionally branch).

- **Lone steward** (n=3): one agent reads both modules and decides.
- **Advice process** (n=3): a decider that has *not* read the code decides from the written advice of
  two module-owner advisor agents (each saw only its own module).

## Result — both avoid the error; the advice process gives the richer decision

| condition | verdict | correct (not naive)? | character |
|---|---|---|---|
| lone steward ×3 | **LEAVE ×3** | yes | conservative — sees the divergence, keeps them separate |
| advice process ×3 | **CONDITIONAL ×3** | yes | actionable — "consolidate only if it branches on order origin", the specific safe design |

Neither condition made the dangerous naive-CONSOLIDATE error. But the two produced *different shapes* of
correct answer. The lone steward, seeing two divergent rules, defaulted to **LEAVE** (safe, conservative).
The advice process produced **CONDITIONAL** — because each advisor stated not just its constraint but its
*acceptance condition* ("acceptable only if it branches on origin"), and the decider found those
conditions compatible, turning "leave it" into a concrete, safe consolidation path.

## What the book should take from this — honest, and it mirrors the program's own finding

- **An LLM proxy cannot demonstrate the advice process *preventing* errors**, because the lone LLM
  steward is already capable enough to catch the conflict in-context (3/3 correct). This is the same
  masking the program documented for human review (`human-review-burden.md`): the model out-performs the
  bounded human, hiding the value that accrues to humans. So P12 must **not** be cited as evidence that
  the advice process reduces error rates.
- **What it does show** is a *quality/shape* effect even for capable agents: distributing the decision to
  module owners surfaced each side's acceptance conditions, yielding a more actionable verdict (the safe
  parameterised merge) than the lone steward's conservative LEAVE.
- **B3 stands as an operating-model recommendation (Ch.11), not an LLM-validated mechanism.** Its real
  value is organisational — distributing knowledge and accountability across the owners who actually hold
  the local constraints, which no single human steward reliably holds. The probe is a demonstration of the
  *structure*, with the honest caveat that the human value is exactly what an all-capable-LLM proxy
  understates.

## Honest caveats
- The constraint conflict is legible in both the code and the docstrings, so the lone steward catches it;
  a larger system where no single reader holds all the local rules is the regime where the advice process
  should pay off, and that regime is not captured here (same context-fits-in-one-head limit as elsewhere).
- n = 3 per arm; advisors were spawned once and their advice reused across decider trials.
- "Correct" = avoided naive consolidation; both LEAVE and the origin-branching CONDITIONAL qualify.

## Artefacts
- `scratchpad/p12/shop/{checkout,admin}/validate.py`; lone-steward, advisor, and decider agent transcripts.

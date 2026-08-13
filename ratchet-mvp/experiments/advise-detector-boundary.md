# Experiment — can the shipped detector close the authoring loop on its own?

**Direction:** the programme's strongest result is the detect-and-revise loop: an agent writes blind
and reinvents a helper, a detector names the collision, the agent is handed the finding and reuses the
canonical helper. That result was produced with a language-model detector that could read the whole
codebase. The shipped `advise` command is deterministic and structural, and the bridge chapter would
naturally present it as the detect step. Whether it can occupy that step is a measurable question and
it had not been measured.

## Method

The ten blind reinventions from the replication run
(`experiments/data/runs/fullcontext/2026-08-12-haiku-4-5/task_only`) are real model output: every one
wrote its own `Decimal`-based conversion and its own retry loop while `billing.money.to_cents` and
`billing.retry.retry` sat in the repository unseen. Each was staged into the fixture in turn and
`coherence-ratchet advise --staged` was run against the derived model.

## Result — 0 of 10

The structural detector named a collision in **none** of the ten. It is not a threshold artefact. A
freshly written conversion and the canonical helper share almost no shingles: the reinventions build
`Decimal(str(x)) * 100` with `quantize` and a `ROUND_HALF_UP` constant, while `to_cents` uses
`to_integral_value`, and the surrounding token streams diverge further. The two functions mean the same
thing and look nothing alike.

The complement holds and marks the other edge of the boundary. Where a change *copies* an existing
helper, as the playground's own copy-and-diverge step does when `loyalty.py` arrives carrying another
retry variant, `advise` names the collision and exits 3, and once a person has ratified the canonical
site the same finding escalates to exit 1.

| what the change did | shipped structural detector |
|---|---|
| copied an existing helper and diverged from it | names the collision |
| reimplemented the same concept from scratch | 0 of 10 |

## What it means

**`advise` is a copy detector, and the loop it closes is the copy loop.** That is worth having, since
copy-and-diverge is the documented drift signature and the case a growing catalogue makes more
frequent. It is not the case the flagship feedback-loop result measured, and the two must not be
conflated.

**The manuscript may not present the deterministic command as the mechanism behind the 0/10 to 10/10
result.** That result needs a detector that reasons about meaning, which in this companion is the
semantic gate. A bridge chapter showing `advise` as the detect step, with the flagship number attached,
would be claiming a loop this measurement says does not close.

**The honest framing splits the loop by detector.** The deterministic floor closes the loop on copies,
cheaply, offline, on every change. The semantic layer is what reaches a reinvention, at the cost of
model calls and a quorum, which is the same division of labour the gate chapter already argues for on
different grounds. This measurement supplies the reason rather than the assertion.

## Honest limits

- One fixture, one task, ten outputs from one dated model snapshot. The direction is not in doubt at
  this n, since the result is 0 of 10 and the mechanism is visible in the token streams, but the
  proportion of real-world reinventions that fall below the threshold is unmeasured.
- The detector was run at the shipped similarity threshold. A lower threshold would not rescue this
  case: the overlap is near zero, not marginal, and lowering it far enough to catch these pairs would
  flood every unrelated function in the tree.
- `advise` was given the derived model and no catalogue. The semantic layer was not in the loop, which
  is the point of the test rather than a limitation of it.

## Reproduce

Stage each `task_only` response into the fixture and run the command:

    cp <run>/task_only/trial-NN.extracted.py billing/charges.py
    coherence-ratchet advise billing --staged --model coherence/selfmodel.json

Needs no API key: the responses are committed and the detector is deterministic.

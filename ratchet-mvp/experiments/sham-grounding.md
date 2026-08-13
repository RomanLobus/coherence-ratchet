# Experiment — does a grounding block work because of what it says, or because of how it sounds?

**Direction:** every grounding result in this programme compares *no grounding* against *correct
grounding*. That design cannot separate two explanations. The block may work because it names the
right helper, or an authoritative-sounding paragraph in an imperative mood may simply make a model try
harder. If the second explanation carries any weight, the derived self-model is partly a placebo and
the method's central artefact is mis-described.

The control is a sham: a block of the same length, register and imperative mood as the real one,
naming helpers that **do not exist anywhere in the fixture**.

```
This subsystem's derived self-model records these CANONICAL helpers you should reuse:
  - currency->cents conversion: `billing.money.to_minor_units(amount)`
  - transient-failure retry:    `billing.resilience.with_backoff(operation, attempts, delay)`
Reuse them; do not reimplement conversion or retry.
```

The fixture's real helpers are `billing.money.to_cents` and `billing.retry.retry`. Neither
`to_minor_units` nor `billing.resilience` exists. The sham was run in two regimes, ten trials each,
`claude-haiku-4-5-20251001` at temperature 1.0, through the committed harness.

## Result — the sham is ignored where the code is visible, and obeyed absolutely where it is not

| condition | subsystem source in context | followed the sham canon | used the real helper | wrote its own |
|---|---|---:|---:|---:|
| `full_sham` | yes | **0/10** | **10/10** | 0/10 |
| `task_sham` | no | **10/10** | **0/10** | 0/10 |

Counts are literal occurrences across the ten committed responses per arm, not scorer inferences: in
the blind arm, ten of ten produced files open with

```python
from billing.money import to_minor_units
from billing.resilience import with_backoff
```

Neither import resolves. Every one of those ten modules fails at import time.

## Replication across a second vendor

The blind arm was re-run on `gpt-5.4-2026-03-05`, ten trials, reported per family.

| family | arm | n | called the non-existent helpers | called the real one |
|---|---|---:|---:|---:|
| `claude-haiku-4-5-20251001` | `task_sham` | 10 | 10/10 | 0/10 |
| `gpt-5.4-2026-03-05` | `task_sham` | 10 | 10/10 | 0/10 |

Identical. A frontier model from a second vendor also imported both fabricated symbols in every
trial, producing ten more modules that fail at import. Compliance with an unverifiable grounding block
is not a quirk of one family.

## What it means

**The placebo explanation is dead, and that is good news for the artefact.** With the subsystem in
context, a confidently worded block asserting a false canon changed nothing: all ten trials read the
code, found `to_cents` and `retry`, and used them. The grounding does not work by sounding
authoritative. Where a model can check, it checks.

**And the same robustness locates the danger precisely.** In the blind arm the block was the agent's
only account of what exists, and all ten complied with it completely. The comparison that matters is
against plain `task_only`, where the same agents with no block at all reinvented the conversion ten
times out of ten. Reinvention is a coherence problem a detector catches at review. Importing a
function that was never written is a broken module, produced with no hesitation, because nothing in
the agent's context contradicted the instruction.

So an unratified model is not inert when it is wrong. It is inert when the agent can see past it, and
authoritative when the agent cannot, which is the reverse of the property anyone would choose. A
grounding pack earns its place exactly in the regime where the system does not fit in the window, and
that is the regime in which nothing checks it. This is the mechanism behind the book's insistence that
only ratified lines may be imperative, measured rather than argued.

**The result also bounds the claim.** It gives no support to a general statement that a derived model
misleads an agent. Where the code was visible the model was harmless, and the manuscript should not
say otherwise. What it supports is narrower and more useful: the harm is conditional on the agent's
inability to verify, which is the ordinary condition at repository scale and the whole reason the pack
exists.

## Honest limits

- Ten trials per arm, one toy fixture. The blind arm replicated identically on a second vendor and is
  near-ceiling in both, so a larger n would tighten the interval without changing the direction. The
  visible arm was run on one family only.
- The sham names are plausible siblings of the real ones. A cruder sham (naming a helper from an
  unrelated domain) would probably be caught more often, and was not tested.
- The visible arm inherits the ceiling effect recorded in `fullcontext-fragmentation.md`: at subsystem
  scale every in-context condition reaches 10/10, so this arm shows robustness to a false block and
  cannot rank correct grounding against no grounding.
- Neither arm speaks to a *partly* wrong block, which is the realistic failure. A model derived from a
  real codebase is mostly right, and whether an agent notices the one stale line among forty accurate
  ones is untested and is the more useful follow-up.
- The agents were not given tools. An agent able to open files would likely have discovered the missing
  module in the blind arm, and the blind arm therefore models a harness without retrieval.

## Where it lands

Chapter 4's opening claim, that a model nobody confirmed can instruct an agent to repeat an accident,
is supported with the scope condition attached: the failure needs an agent that cannot check. Any
sentence claiming a wrong model misleads unconditionally is contradicted by the `full_sham` arm and
must be qualified.

## Reproduce

    python3 experiments/harness/dispatch.py --probe probe_fullcontext_fragmentation.py \
        --condition full_sham --condition task_sham --trials 10 \
        --model claude-haiku-4-5-20251001 \
        --out experiments/data/runs/fullcontext/2026-08-12-sham

Raw responses, extracted modules and the run manifest are committed under that path. Scoring re-runs
offline with `--rescore` and needs no API key.

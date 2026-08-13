# Experiment — the author, detect, revise loop, from a committed harness

**Direction:** `feedback-loop.md` is the programme's strongest result and one of its least checkable.
An agent given a task but not the file holding the canonical helper reinvented the conversion in all
ten trials; a detector that could see the codebase named the collision in all ten; handed the finding,
the agent reused the helper in all ten. The prompts, the returned code and the detector all lived in a
session nobody else could re-enter.

Two things had to exist before it could be re-run. The harness was single-shot, so it could not
express a loop at all; it now supports a second round in which a probe inspects the first response,
makes its own model call, and returns a revision prompt. And the detector had to be chosen on
evidence: `advise-detector-boundary.md` measured the shipped deterministic detector naming a collision
in **none** of ten real reinventions, because a freshly written `Decimal.quantize` conversion and the
canonical `to_integral_value` helper share almost no structure. The loop closes only with a detector
that reasons about meaning, which is what the original used.

## Setup

    round 1   the agent writes `billing/charges.py`; the canonical helpers are not in its context
    detect    a separate call sees the subsystem source and the produced module, and is asked to name
              any duplication in the form `DUPLICATES <name>: <what>`, or to answer NONE
    round 2   the finding is handed back with the original task and the produced code, and the agent
              revises

Both rounds are scored by the same deterministic scorer, so the result is a before and an after on
the same trial. Ten trials, `gpt-5.4-2026-03-05`.

## Result — 0/10 before, 10/10 after

| stage | count |
|---|---:|
| reuse of both canonical helpers, before feedback | **0/10** |
| detector named a collision | **10/10** |
| reuse of both canonical helpers, after feedback | **10/10** |

The original figure reproduces exactly, on a different vendor from the one that produced it, with
every prompt, response and detector call committed.

## What it means

**The loop is a shipped, checkable procedure rather than a transcript.** Anyone with a key can re-run
it; anyone without one can re-score the committed responses and dispute the scorer.

**Detection after the fact replaces prediction before it, and that is the whole economy of the
result.** Prevention has to guess which helper a task will need before the work starts, and the guess
gets harder as a catalogue grows. Detection only has to answer whether the code just written collides
with something that exists. Nothing was surfaced in advance here and reuse still went to ten out of
ten.

**The detector is the semantic layer, and the manuscript must attribute it that way.** The
deterministic command reaches copies and does not reach this case. A chapter presenting `advise` as
the mechanism behind this number would be claiming a loop the boundary measurement says does not
close.

## Honest limits

- **Round two is a reconstruction, not a continuation.** The original fed the finding into a live
  session. This harness has no session, so round two is a single prompt carrying the task, the code
  the agent produced, and the finding. An agent with true conversational memory may behave
  differently, and the difference is untested.
- The detector is the same model family as the author, which is faithful to the original and means the
  result says nothing about a detector that is weaker or differently trained. Cross-family judging is
  the obvious variant and was not run here.
- Ten trials, one fixture, one task, a 1:1 mapping between the task and the helper it needs. Real
  changes need several helpers, some of which fit only partly, and `reframe-D-coherence-price.md`
  found reuse moving far less in the partial-fit case.
- The detector saw the whole subsystem. At repository scale it faces the retrieval limit every other
  part of this method faces, and this fixture is too small to show it.

## Reproduce

    python3 experiments/harness/dispatch.py --probe probe_feedback_loop.py \
        --trials 10 --model gpt-5.4-2026-03-05 \
        --out experiments/data/runs/feedbackloop/2026-08-12-gpt-5.4
    python3 probe_feedback_loop.py --tally experiments/data/runs/feedbackloop/2026-08-12-gpt-5.4

Each trial commits its first-round code, the detector exchange, and the revised module.

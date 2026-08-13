# Experiment #1 — In-loop self-correction feedback

**Hypothesis (open direction #1):** prevention (surface the catalogue up front) requires predicting which abstraction is relevant — the retrieval-quality problem H1 left open. A different lever: let the agent write the change, *detect* the coherence damage on its output, and feed it back so it self-corrects — no prediction needed, because duplication is detectable after the fact.

**Result: feedback flipped reinvention to reuse completely — 0/10 → 10/10 — without ever surfacing the helper up front.** It works because the detector catches the collision *after* the agent writes it, sidestepping the prediction problem that bounds prevention.

## Re-run from a committed harness, 12 August 2026

`feedback-loop-harnessed.md` reproduces this result end to end with every prompt, response and
detector call committed: 0/10 reuse before feedback, the detector naming the collision 10/10, and
10/10 reuse after, on a different vendor. Two conditions were established first. The harness
gained a second round, and the detector had to be the semantic layer, because
`advise-detector-boundary.md` measured the deterministic detector reaching none of ten real
reinventions. Round two there is a reconstructed prompt rather than a continued session.

## Design (author → detect → revise, all pre-commit)
A `money.py` with a canonical `to_cents(amount)` exists in the codebase. The implementer agent is given **only the task** ("write `charge_customer` that converts dollars to cents and calls the gateway") — *not* `money.py` — modelling the realistic case where an agent cannot see the whole system (the root cause). Then:
- **Round 1 (control):** implementer writes it blind. (10 trials)
- **Detect:** a detector agent, which *does* see the full codebase + the new code (like CI or a reviewer running after the commit), reports whether the new code duplicates something that exists.
- **Round 2 (feedback):** the detector's finding is fed back; the implementer revises.

## Results

| Stage | Outcome |
|---|---|
| Round 1 — task only, no surfacing | reuse `to_cents` **0/10**; reinvented the conversion inline **10/10** |
| Detector — flagged the duplication | **10/10** (correctly named `to_cents`, noted the inline Decimal/ROUND_HALF_UP reimplementation) |
| Round 2 — after detector-driven feedback | reuse `to_cents` **10/10** |

## What it shows
- **Feedback-on-output is a working lever, distinct from prevention.** Reuse went 0 → 10/10 with the helper never surfaced before authoring. The agent reinvented (it couldn't see the system), the detector caught it, the agent fixed it.
- **It sidesteps the retrieval problem that bounded prevention.** H1 showed prevention's open weakness is *predicting* which of many catalogue entries to surface for a change. Feedback needs no prediction: you let the change happen, *detect the actual duplication* (which the validated concept-detector does reliably — H5), and feed the specific collision back. The hard "surface the right entry in advance" problem is replaced by the easier "detect the collision after" — which the method already does well.
- **It is the ratchet as an in-agent loop.** Author → detect → revise, before commit, is the ratchet's hold-or-lower logic run as the agent's own self-correction rather than a human-steward gate downstream. It left-shifts consolidation into the authoring loop without needing the agent to be omniscient.
- **It composes with prevention, doesn't replace it.** Prevention stops the divergence you can predict (surface the obvious helper); feedback catches the rest (detect what slipped through). Together: surface what you can, detect-and-correct what you couldn't.

## Honest caveats
- Toy 1:1 mapping (one task, one helper, exact reimplementation), Claude/Python, n=10 — the detector's job here was easy (a near-verbatim duplicate). At scale the feedback's value rides on the detector's precision/recall (H5: high at moderate scale, but precision-at-scale is the open limit) and on the feedback being specific enough to act on.
- Adds a detect-and-revise round-trip per change — a real cost, justified when the change touches coherence-sensitive areas, not every commit.
- The detector saw the full codebase here; at scale it faces the same context/sharding limit as H1/H5 (it can't read everything at once), so feedback inherits that boundary — though detecting a *specific* new duplicate is narrower than scanning the whole repo.

## Verdict
In-loop self-correction works and is the most promising of the open levers: detector-driven feedback on the agent's own change lifted reuse 0 → 10/10 with no up-front surfacing, turning prevention's hard prediction problem ("which helper is relevant?") into the method's easy detection problem ("does this new code collide with something?"). It belongs in the method as a left-shifted, pre-commit self-correction loop — author, detect, revise — composing with prevention (predict what you can) and the steward gate (judge what's left).

→ book: a new beat in Ch.7 (the ratchet runs inside the authoring loop, not only at review) and Ch.3/prevention (feedback complements surfacing — detect-after where predict-before fails). Caveats inherit the detector's precision-at-scale limit. n=10 toy; multi-task and at-scale versions logged as future work.

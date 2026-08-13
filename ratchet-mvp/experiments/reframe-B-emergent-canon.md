# Reframe B — Emergent, ratified canon: sound, or entrenches a bad majority?

**Rescoped by A's gate:** the derived self-model surfaces candidate patterns; B tests whether **ratifying the modal pattern** (the one the code/agents converge on) yields a *sound* canon — letting the steward *ratify* (cheap, auto-fresh) instead of *author* (expensive, rots) — or whether it would entrench a popular-but-wrong pattern.

**Result: across four concepts with real correctness traps, the modal pattern was sound every time — 10/10 implementations passed the correctness oracle for each concept, and convergence was near-total. So ratifying the emergent canon is safe for common, well-understood concepts. The entrenchment risk (a popular-but-wrong majority) was not triggered here, so it remains a real-in-principle reason to keep a steward veto — "ratify with veto", not blind auto-ratify.**

## Results (10 implementations per concept, run against a correctness oracle)

| Concept | Trap | Modal pass rate | Verdict |
|---|---|---|---|
| `to_cents` | float `*100` loses money (19.99→1998) | **10/10** (all used `Decimal`/`ROUND_HALF_UP`) | sound |
| `parse_bool` | only handling `"true"`, missing `yes`/`y`/`1` | **10/10** (all used a full truthy set) | sound |
| `chunk` | erroring on an empty sequence | **10/10** (all handled `[]`→`[]`) | sound |
| `retry` | swallowing the error / returning `None` instead of re-raising | **10/10** (all re-raised the last exception) | sound |

Convergence was strong, not just correct: `chunk` was the *same* comprehension in 10/10, `retry` the same `last_exc` loop in 10/10 — there is a real modal pattern to ratify.

## What it means
- **Ratifying the emergent canon is safe for common concepts.** The majority converged on the correct pattern for every trap tested — including the float-money trap agents *could* have fallen into and didn't. So the steward can **ratify the modal pattern the self-model derives** rather than author a catalogue by hand. Combined with A, this is the second half of dissolving the method's biggest risk.
- **Together, A + B reduce the catalogue-staleness problem (R4) and the steward's freshness duty (R10).** A makes observations regenerable and revision-bound; B supplies candidates whose frequency is evidence, not authority. A person may ratify a candidate with scope, rationale, provenance, and affected-owner advice. The experiment supports candidate generation for these common concepts; it does not establish a canon automatically.

## Honest caveats — the entrenchment risk is untriggered, not disproven
- **Four common, well-understood concepts, all of which converged sound.** These are concepts whose correct pattern is well-represented in training data, so agents converge on it. I did **not** find or test a concept where the *popular* pattern is *wrong* (naive email regex, naive UTF-8 truncation, string-built SQL). On such a concept the modal would be popular-but-wrong, and blind ratification would entrench the bug. So "the modal is sound" is shown for common concepts, **not** proven universal.
- **Therefore the safe rule is ratify-with-veto:** the steward ratifies the derived modal by default (cheap, fresh) but retains a veto for the long tail and known-bad-but-popular patterns. That keeps the freshness win while covering the entrenchment risk.
- n=10 per concept, Claude/Python, correctness-oracle grading (objective, not opinion).

## Gate decision
**Adopt emergent-ratified canon, with a steward veto.** For the chain: D computes its coherence score against the self-model's *ratified* canon; C's convergence result (does decentralised negotiation reach the same modal?) is the decentralised counterpart of this finding. The book's steward becomes a *ratifier and judge*, not an author and refresher.

→ book: Ch.3/Ch.11 — the canonical pattern is *derived and ratified* (steward ratifies the modal the self-model surfaces, with a veto for bad-but-popular patterns), not hand-curated; this, with A's derived self-model, is the honest resolution of the R4 staleness risk and the R10 freshness duty — the steward's hardest duty becomes a light one. Caveat in the limits thread: the entrenchment case (popular-but-wrong) is real and the veto exists for it; tested concepts were all common/sound, so the universal claim is not made.

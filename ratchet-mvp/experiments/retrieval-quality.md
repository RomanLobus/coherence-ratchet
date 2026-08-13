# Experiment H1 — Retrieval quality: does prevention survive a larger, noisier catalogue?

**Hypothesis (defends E1):** E1b's 0→100% reuse swing used a 1:1 task-to-helper mapping. With a realistic catalogue you cannot surface everything, so prevention should degrade to a *retrieval-quality* problem — does the system put the right entry in front of the agent, and does reuse survive volume and noise?

**Result: in the regime these probes can reach, retrieval and reuse are robust — I tried twice to break them and could not. The real open problem is narrower and sharper than "does retrieval work": it is scale beyond the context window and genuine ambiguity, neither of which a full-list LLM ranker addresses.**

The task was held fixed (charge a customer; it needs a dollars→integer-cents conversion — one genuinely relevant helper) while how that helper was presented varied. n=10 per condition.

## Run 1 — obvious match (`to_cents`), catalogue of 24

| Condition | Reuse of the helper |
|---|---|
| control (no catalogue) | **0/10** — all reinvented the conversion inline (Decimal/round) |
| flood-5 (helper + 4 others) | **10/10** |
| flood-24 (helper buried among 24) | **10/10** — burying it among 24 did *not* reduce reuse |
| retrieve top-3 (LLM ranker picks 3 of 24) | recall@3 **10/10**, reuse **10/10** |

## Run 2 — semantic gap (helper renamed `to_minor_units`, ISO-4217 jargon; task still says "cents"; lexical traps `centroid`, `percent_change`, `percent_of` present)

| Condition | Reuse of the helper |
|---|---|
| control | **0/10** (reinvented inline) |
| flood-5 | **10/10** |
| flood-24 | **10/10** |
| retrieve top-3 | recall@3 **10/10**, reuse **10/10**, trap-helper calls **0/10** |

The LLM ranker bridged "cents" → "smallest minor unit (ISO 4217)" every time and ignored the helpers that merely *contained* the letters "cent". The vocabulary gap and the lexical traps did not dent it.

## What it means
- **Prevention is robust to a moderate catalogue.** Reuse held at 24 entries exactly as at 5, and held across a deliberate task-to-helper vocabulary gap. At the scale a context window comfortably holds, "surface the catalogue" is not fragile — the agent finds and reuses the right helper whether it is surfaced among 5, buried among 24, or selected by a ranker.
- **An LLM ranker is a strong retriever at small scale.** recall@3 was perfect in both runs, including across the semantic gap. For tens of entries, retrieval is not the bottleneck E1's caveat feared.
- **So the open problem is relocated, not closed.** These probes deliberately had *one* clearly-correct helper and a catalogue that fits in context. The retrieval risk the book should name lives in the two regimes I could not cheaply test: (1) **scale past the context window** — hundreds to thousands of entries, where you cannot surface all of them and an LLM-over-the-full-list ranker no longer scales, so a real vector/keyword index is required (and its recall, not the model's, becomes the gate); and (2) **genuine ambiguity** — several partially-fitting helpers with no single right answer, where "top-3" can be wrong in ways this single-answer design cannot show. That is a sharper, more honest statement of the open problem than "retrieval is hard."

## Honest caveats
- **I could not produce the failure the hypothesis predicted**, because the test regime (≤24 entries, one relevant helper) is below where retrieval breaks. The negative space — large catalogues, ambiguous fits — is exactly what was not tested, and the write-up says so rather than implying retrieval is universally solved.
- The LLM ranker reads the *whole* catalogue each call; that is what fails at scale (cost and context), so the small-scale perfection does not transfer to thousands of entries.
- Claude-only, Python, n=10, structural reuse detection (`to_cents(` / `to_minor_units(`), single task. Reuse classification is binary by design.

## Verdict
Retrieval-driven prevention is robust where it was testable: a 24-entry catalogue and a task-to-helper vocabulary gap both left reuse at 10/10 and ranker recall@3 at 10/10. The honest correction to E1's caveat is that retrieval is *not* the weak point at small scale — it is at large scale (past the context window, requiring real index infrastructure whose recall becomes the true gate) and under genuine ambiguity (many partial fits). The book should pose the open problem at that precise boundary, and stop short of claiming either that retrieval is a non-problem (it will be, at scale) or that small-catalogue prevention is fragile (it is not).

→ book: tightens the prevention sections (Ch.3/Ch.7) — surfacing works robustly for moderate catalogues; the "retrieval quality is the open problem" framing in the closing chapter is sharpened to *scale past context + ambiguity*, naming real index infrastructure as the requirement and its recall as the gate. A new dead-end nuance: "a large catalogue or a vocabulary gap breaks prevention" — not at the scale tested; the break is at context-exceeding scale, untested here.

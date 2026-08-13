# coherence-ratchet

**Measure what a change does to the shape of a codebase, put the structure you have authorised where
coding agents will read it, and hold a line against new structural worsening — starting from the
tangle you already have.**

AI-assisted development makes code cheaper to produce without making a long-lived system cheaper to
change. A pull request passes review, tests, and deployment, and still leaves behind one more local
workaround, a second way of expressing the same rule, or a dependency nobody meant to create.
Repeated across months, those individually safe changes accumulate into **coherence debt**: the
structural cost carried by software that still works and is steadily harder to understand,
coordinate, and evolve. Gates that watch behaviour cannot see it arriving, because nothing has
broken.

This is a **reference implementation**, deliberately minimal and subsystem-scale by design. It is
not a product, and it does not automate architectural judgement: every mechanism surfaces a decision
to a person rather than making it.

## Install

```sh
pip install coherence-ratchet
```

Zero runtime dependencies, Python 3.10+. The deterministic floor needs no LLM and no network; the
semantic layer is optional and env-gated on an API key.

## The loop

> derive → ratify → ground → author → detect → hold → judge

```
measure     the signal portfolio for a tree
init        write the baseline budget from that portfolio
check       fail if coherence worsened past the budget; --accept records owned debt
selfmodel   derive facts, query evidence, ratify intent, render context
ground      write ratified intent into the files coding agents read; --check verifies it is current
advise      measure a staged change against the existing code, return a revision instruction
serve       expose ratified intent to coding agents over MCP (stdio)
gate        the optional LLM semantic layer over the deterministic residue
compare     bounded behavioural comparison of a consolidation
apidiff     diff the public API surface of two trees
report      exposure and ownership report over the coherence-debt ledger
close       close open ledger entries for a region (appends, never edits)
history     sample the signal portfolio across committed history
calibrate   sample function pairs for labelling, report the threshold curve
import      read another tool's measurement as candidate counts
```

## Three properties worth knowing before you run it

**Observation is not authority.** `selfmodel derive` records what the code demonstrably contains and
what the extractor merely inferred, kept apart. A pattern repeated fifty times is still a candidate.
`selfmodel ratify` is the only path from candidate to ratified intent, and only ratified intent may
instruct an agent. Every rendered statement is labelled `[OBSERVED]`, `[CANDIDATE]` or `[RATIFIED]`.

**The ratchet is a delta instrument.** `init` baselines today's tangle rather than demanding a
cleanup first, and `check` trips only on new worsening. Accepted deterioration needs an owner, a
repayment trigger, a review date, evidence, confidence, all five exposure dimensions and repayment
feasibility. Exposure is five ordinal dimensions with no summed score and no currency estimate,
because a single number invites a false trade against delivery.

**There is no `PROVED`.** `compare` reports `REFUTED`, `NO_DIVERGENCE_FOUND` or `UNPROVEN`. The
absence of a counterexample in a bounded space is not a proof, and the tool declines to print a word
that could be read as one.

## Honest limits

The similarity threshold shipped here was tuned against this repository's fixtures
(`MIN_TOKENS = 12`, `SHINGLE_K = 5`, `SIM_THRESHOLD = 0.45`); a real codebase needs its own, and
`calibrate` is how to get it. The detector is O(n²) pairwise, which is fine at subsystem scale and
not at repository scale. Coupling is reported and never ratcheted, because consolidation legitimately
raises coupling to a shared helper. The extractor is Python, though the judgement model is not:
`import` reads another tool's counts. Martin's main-sequence distance was measured, found to carry
no information for Python, and retired; the negative result is kept rather than quietly dropped.

Output formats are frozen per minor version and `CHANGELOG.md` records every change to a printed
format, so anyone quoting this tool's output can pin the version that produced it and tell a version
gap from a defect.

The repository carries the quickstart, the experiment record with its negative results, a bounded
formal lab, and a cross-language seam lab: <https://github.com/RomanLobus/coherence-ratchet>

MIT licensed.

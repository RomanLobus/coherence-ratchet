# coherence-ratchet

The reference implementation for the book *Coherence Debt: Keeping Software Worth Changing When AI
Writes the Code*. It is an existence proof that the book's method is buildable and runnable, and it
is deliberately minimal: a companion to the book, **not a product to adopt in place of the method**.

It exists to make one claim checkable: design-coherence decay under AI-authored change is
measurable, and a ratchet can hold it.

The method is one loop of seven stations:

> derive → ratify → ground → author → detect → hold → judge

The deterministic floor needs no LLM, no network, and no dependency beyond the Python standard
library. The semantic layer is optional, env-gated on an API key, and never acts on its own.

## Install

```sh
pip install coherence-ratchet
```

Or from a clone of the companion repository, which is the route the book prints:

```sh
git clone --branch v0.5.0 --depth 1 https://github.com/RomanLobus/coherence-ratchet
cd coherence-ratchet
python3 -m pip install ./ratchet-mvp
python3 ratchet-mvp/tests/run.py        # 201 tests, offline
```

## The command surface

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
what the extractor merely infers, kept apart. A pattern repeated fifty times is still a candidate.
`selfmodel ratify` is the only path from candidate to ratified intent, and only ratified intent may
instruct an agent. Every rendered statement is labelled `[OBSERVED]`, `[CANDIDATE]` or `[RATIFIED]`.

**The ratchet is a delta instrument.** `init` baselines today's tangle rather than demanding a
cleanup first, and `check` trips only on new worsening. Accepted deterioration needs an owner, a
repayment trigger, a review date, evidence, confidence, all five exposure dimensions and repayment
feasibility. Exposure is five ordinal dimensions with no summed score and no currency estimate.

**There is no `PROVED`.** `compare` reports `REFUTED`, `NO_DIVERGENCE_FOUND` or `UNPROVEN`. The
absence of a counterexample in a bounded space is not a proof, and the tool declines to print a word
that could be read as one.

## Honest limits

The similarity threshold shipped here was tuned against this repository's fixtures
(`MIN_TOKENS = 12`, `SHINGLE_K = 5`, `SIM_THRESHOLD = 0.45`); a real codebase needs its own, and
`calibrate` is how to get it. The detector is O(n²) pairwise, which is fine at subsystem scale and
not at repository scale. Coupling is reported and never ratcheted, because consolidation legitimately
raises coupling to a shared helper. Martin's main-sequence distance was measured, found to carry no
information for Python, and retired; the negative result is kept rather than quietly dropped.

Output formats are frozen per minor version and `CHANGELOG.md` records every change to a printed
format, so a reader who finds this tool disagreeing with a printed block in the book can tell a
version gap from a defect.

Full documentation, the quickstart, the experiment record, the formal lab and the enterprise seam lab
are in the repository: <https://github.com/RomanLobus/coherence-ratchet>

MIT licensed.

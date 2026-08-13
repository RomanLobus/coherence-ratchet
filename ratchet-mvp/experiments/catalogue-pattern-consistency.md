# Experiment — catalogue-based pattern consistency (closing P5's loop)

**Direction:** P11. P5 found the MMI's third dimension — **pattern consistency** — could not be computed
from the dependency graph: the deterministic proxy (instability variance) was weak and even misleading
(flask read "consistent" because it was *uniformly* tangled), and P5 concluded the real signal needs the
catalogue/LLM gate. This probe tests that directly. Two fixtures: **coherent** (a concept — retry —
implemented 5× following one canonical pattern) and **fragmented** (the same concept implemented 5
divergent ways: while-loop, recursion, no-backoff, error-swallowing, single-shot). Pattern-consistency is
scored two ways — the deterministic duplication proxy, and an LLM catalogue-match gate (3 trials).

## Result — the deterministic proxy inverts; the catalogue-match gate is correct

| signal | coherent fixture | fragmented fixture |
|---|---|---|
| deterministic **duplication** ratio | **1.00** (flagged "redundant" = bad) | **0.00** (looks "clean" = good) |
| LLM **catalogue-match** consistency (3 trials, unanimous) | **5/5 conform = 1.00** | **0/5 conform = 0.00** |

The duplication signal is **exactly inverted** as a consistency measure: the coherent codebase (five
identical canonical retries) scores maximal duplication and looks *bad*; the fragmented codebase scores
zero duplication and looks *clean*. This is the flask inversion (`architecture-decay.md`) in miniature
and sharp. The **catalogue-match gate scores them correctly and unanimously** across 3 trials —
coherent 1.0, fragmented 0.0 — and each trial named the specific divergence per function (swallows the
error, no backoff, recursion, raises a generic error instead of the original).

Plugged into the MMI composite, pattern-consistency therefore behaves as intended only when computed via
the catalogue: 1.00 for the coherent system, 0.00 for the fragmented one — whereas the deterministic
proxy would have *rewarded* the fragmented system.

## What the book should take from this

- **Ch.6 / Appendix A (and closing P5):** MMI's pattern-consistency dimension is **recoverable, but only
  through the catalogue-match LLM gate** — not from any dependency-graph or duplication statistic. The
  deterministic proxy is not merely weak, it is sign-inverted for this dimension.
- **Reinforces the central thesis (P5, P8):** the catalogue is the load-bearing artefact. The one MMI
  dimension that adds signal beyond the dependency graph is exactly the one that requires the
  human-curated catalogue + constrained LLM matcher the book is built around. Pattern consistency =
  *conformance to the catalogue*, which is the gate the method already defines.
- It also gives MMI a complete first-party implementation path: modularity + hierarchy from
  `archmetrics`, pattern-consistency from the catalogue gate.

## Honest caveats
- One concept (retry), 5 + 5 implementations, 3 gate trials (unanimous, so high agreement — but a clean,
  well-separated case, like `semantic-detector.md`'s easy regime). Fine-grained / borderline conformance
  is untested and is where multi-trial voting matters.
- The canonical pattern was handed to the gate; deriving/ratifying it is the catalogue's own job
  (`reframe-B-emergent-canon.md`).
- Reintroduces the LLM into measurement, so it inherits the gate's reliability caveats and cost.

## Artefacts
- `scratchpad/p11/coherent.py`, `fragmented.py` (+ `_pkg` copies for the deterministic measure).

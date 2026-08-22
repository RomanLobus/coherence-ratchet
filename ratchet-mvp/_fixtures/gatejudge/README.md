# Fixture: the eight `requests` clusters the consolidation judge was asked about

These are the function bodies `probe_gate_judge.py` sends to the judge. They are committed rather than
read from an installed `requests` for one reason: a pip-installed library moves, and a judge that sees
different text on different runs is not being replicated, it is being asked a new question each time.

**Source.** Extracted by AST from `requests` **2.34.2**, on 13 August 2026, by walking each module's
syntax tree for the named function and taking its decorators through to its last line. Nothing was
edited, reformatted, or re-indented, which is why the four `*_utf8` helpers carry the indentation of
the enclosing `build_digest_header` they are defined inside.

**Cluster membership and ground truth** come from
`ratchet-mvp/experiments/semantic-gate-on-requests.md`, which enumerates all eight clusters with their
members and hand-assigned labels. That record is what makes this probe a replication rather than a new
experiment; the reconstructability audit in `EXPERIMENT-INDEX.md` records why the other three Tier 1
experiments could not be rebuilt the same way.

**One honest gap.** The original run's `requests` revision was not recorded. These snippets come from
2.34.2, which is almost certainly a later version than the one the original judge saw. Four of the
eight clusters are stable public API that has not changed shape in years; C3's helpers now carry
`usedforsecurity=False` and type annotations that the original may not have had. A re-run therefore
tests the same *clusters* and not byte-identical *inputs*, and that limitation belongs in the result
rather than in a footnote nobody reads.

Two members of C2 duplicate module-level helpers already present in C1, so twenty files cover
twenty-two member slots.

# Changelog

Output formats are part of the contract: the book renders this tool's output verbatim, so any
change to a printed format bumps the version, and the book states which version produced its
numbers.

## 0.1.0 — 2026-07-10

First public release. The reference implementation as validated for the book *Coherence Debt:
Keeping Software Worth Changing When AI Writes the Code*:

- `measure` / `init` / `check` — the deterministic floor: function-level duplication clusters,
  dependency cycles, coupling density, fan-in, connascence of shared literals, held against a
  per-region budget with an owned, dated ledger (`--accept`).
- `selfmodel derive` / `query` / `context` — the derived, queryable self-model and the
  agent-grounding pack rendered from it.
- `gate` — the optional LLM catalogue-matcher (offline by default; surfaces to a human, never
  auto-blocks).
- `prove` — the behaviour-complete proof: property-based differential testing of a proposed
  consolidation against each original.
- `report` — leading indicators read from the ledger (coverage, overdue items, how long the
  ratchet has held).
- The five-state billing playground, the consolidation/fullcontext/stampy fixtures, 58
  experiment write-ups with their scripts, and the recorded longitudinal architecture data.

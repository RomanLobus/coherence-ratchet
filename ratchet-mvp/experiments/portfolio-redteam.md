# Experiment — portfolio sufficiency red-team

**Direction:** P8 (stress-tests this research's own fix). P4 killed the single-metric (cycle-only)
ratchet and recommended a **multi-signal portfolio** (cycles + duplication + connascence, = B8). That
recommendation was asserted, not tested. This probe red-teams it: five agents were told to reimplement
a money-to-cents + retry capability *without* reusing the canonical helpers and to **pass all three
deterministic gates at once** — no import cycle, no structural-clone match, no shared magic literal.
Question: can an author fragment while satisfying the whole deterministic portfolio?

## Result — the deterministic portfolio is gameable, 5/5

Verified with the project's own tools (`metrics`, `archmetrics`, `probe_connascence`) on each produced
`discount.py`:

| trial | cycles | structural-dup vs canonical | shared literals | rounding mode | all 3 gates pass? |
|---|---|---|---|---|---|
| t1 | 0.0 | none | 0 | ROUND_HALF_EVEN | **yes** |
| t2 | 0.0 | none | 0 | floor(x+0.5) over float | **yes** |
| t3 | 0.0 | none | 0 | ROUND_HALF_EVEN | **yes** |
| t4 | 0.0 | none | 0 | ROUND_HALF_UP | **yes** |
| t5 | 0.0 | none | 0 | ROUND_HALF_EVEN | **yes** |

All five produced a **semantic duplicate** of the canonical helpers that passes the entire deterministic
portfolio: they varied control flow (recursive vs `while`-countdown vs slot-tuple retry) to dodge the
clone detector, and spelled constants as expressions (`10 ** 2`, `6 // 2`, `Decimal("1e2")`,
`len((slot,))`, `40.0/1000.0`) to dodge the connascence-of-meaning check. None created a cycle.

**Worse: 4 of 5 introduced a *different rounding mode* than the canonical `ROUND_HALF_UP`** (three
bankers'-rounding, one float `floor(x+0.5)`). That is a **silent behaviour divergence** — the exact
silent-rounding-mode failure the integrator probe flagged — and it is invisible to all three
deterministic signals. Only t4 happened to match the canonical rounding.

## What this means for the book — it tempers my own P4 recommendation

- **The multi-signal portfolio (B8) is necessary but NOT sufficient.** It raises the bar over a single
  metric (P4), but a determined or out-of-context author still slips a semantic duplicate past all of
  it — and can carry a behaviour divergence while doing so. So the portfolio is a *floor*, not the
  whole gate.
- **This reinforces the book's existing architecture rather than undermining it.** The two layers that
  *do* catch what the deterministic portfolio misses are already in the method: the **LLM semantic
  detector** (catches divergent reimplementation — `semantic-detector.md`) and the **behaviour-complete
  proof** (catches the rounding divergence — `autonomous-consolidation.md`). P8 shows precisely why
  both are load-bearing, not optional polish: remove them and a fragmenting change is invisible.
- **Net framing for Ch.7/Ch.10:** deterministic signals (cycles + duplication + connascence) are the
  cheap first pass; the semantic detector + the proof are what make the gate sufficient. The ratchet
  story is "portfolio *then* semantic *then* proof," and the honest limit is that no purely
  deterministic gate is game-proof.

## Honest caveats
- The prompt was explicitly adversarial ("evade these gates"). That models the worst case and the
  out-of-context author, not typical behaviour — P4 showed in-context agents *reuse* rather than fight
  the gate. The claim is "the deterministic portfolio *can* be evaded," an existence result, not a rate.
- The clone detector is the MVP AST-shingle one; the connascence check is literal-overlap. A stronger
  Type-4 detector is exactly the LLM semantic pass — which is the point (the deterministic layer alone
  is insufficient).
- n = 5; single capability; toy package.

## Artefacts
- `scratchpad/p8/trial1..5/shop/discount.py` — verified against the three gates with the project tools.

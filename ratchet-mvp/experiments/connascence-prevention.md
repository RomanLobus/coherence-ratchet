# Experiment — connascence of meaning as a prevention lever

**Direction:** P10 (P3 + Page-Jones's own rule "minimise connascence across boundaries", and a direct
follow-up to P8). P8 showed agents readily produce a *divergent rounding mode* when reimplementing.
P10 asks: does **surfacing the existing convention at authoring time** prevent that connascence-of-meaning
divergence? An agent adds a discount-rounding function to a `shop` package whose `money` module fixes a
rounding convention. Control: neutral task. Treatment: "round consistently with the convention used by
this package's `money` module." Two regimes: the convention is the agent's **default** (ROUND_HALF_UP),
then a **non-default** one (ROUND_HALF_EVEN, banker's).

## Result — surfacing prevents the divergence exactly where it can occur

| Regime | condition | rounding mode | conforms? | reused `money` helper? |
|---|---|---|---|---|
| canonical = HALF_UP (default) | control ×5 | HALF_UP ×5 | yes (by default) | **reinvent ×5** |
| canonical = HALF_UP (default) | treatment ×5 | HALF_UP ×5 | yes | **reuse ×5** |
| canonical = HALF_EVEN (non-default) | control ×3 | **HALF_UP ×3** | **DIVERGE ×3** | reinvent ×3 |
| canonical = HALF_EVEN (non-default) | treatment ×3 | **HALF_EVEN ×3** | **conform ×3** | reuse ×3 |

Two clean effects:

1. **Connascence of meaning (the convention/value).** When the codebase's convention is the agent's
   own default (HALF_UP), there is **nothing to prevent** — control conforms anyway (5/5). But when the
   codebase chose a **non-default** convention (banker's rounding), control **silently diverges 3/3**:
   every agent reaches for HALF_UP, the conventional default, quietly breaking the codebase's HALF_EVEN
   choice. Surfacing the convention prevented **all** of it (3/3 conform). This is the silent
   rounding-mode divergence P8 induced, now shown to be a *default-vs-convention gap* — and surfacing
   closes it.

2. **Connascence of algorithm (the helper).** In every regime, control **reinvented** the converter
   inline (a fresh duplicate) while treatment **reused** `money.to_cents` (0/5 → 5/5, reinvent → reuse).
   So even when the value doesn't diverge, surfacing the convention prevents duplicate implementation.

## What the book should take from this

- **Ch.3 (prevention front-end) + Ch.7:** extend "visibility is the lever" (E1) from *helpers* to
  *conventions and magic values* — surfacing the canonical convention prevents connascence of meaning,
  not just connascence of algorithm. The catalogue/self-model should carry **conventions** (rounding
  mode, tier rates, status vocab), not only reusable functions.
- **The honest scoping (and it sharpens the method):** prevention-by-surfacing matters for
  **non-default** conventions the agent will not guess. Where the codebase's choice coincides with the
  model's default, divergence does not arise and surfacing is redundant for the *value* (though it still
  drives helper reuse). So the steward's catalogue earns its keep precisely on the **non-obvious**
  conventions — the ones a fresh agent reaches past toward its prior. Ties to P8: the dangerous silent
  divergences live exactly there.

## Honest caveats
- Single convention (rounding mode); n = 5 (base) + 3 (contingency) per arm; toy package.
- The treatment pointer named the `money` module, so part of the effect is discoverability (P7) — but
  the *value*-conformance result (HALF_EVEN 3/3 vs HALF_UP 3/3) is specifically about adopting the
  convention once seen, which is the connascence-of-meaning point.
- Agents here can read the package; a no-search regime would diverge even in the default case.

## Artefacts
- `scratchpad/p10/` (HALF_UP canonical, 5+5) and `scratchpad/p10b/` (HALF_EVEN canonical, 3+3).

# Experiment — connascence as a fragmentation signal

**Direction:** B1 (corpus pass). Page-Jones's connascence (Fundamentals Ch.3, BEA Ch.5) is a taxonomy
of coupling — static (name < type < meaning < position < algorithm) and dynamic — each ranked by
**strength × locality × degree**, with the rule that *distant* connascence is worse than local. The
book's signals (duplication, cycles, coupling, fan-in) already capture connascence of *algorithm*
(same idea reimplemented) and *name* (imports), but are **blind to connascence of meaning**: the same
magic value or convention hard-coded across modules — an implicit agreement that breaks silently when
one site changes. This probe (`probe_connascence.py`) (A) builds a connascence-of-meaning detector and
(B) re-weights the existing duplicate clusters by locality × degree.

## Result A — connascence of meaning is a real, cheap signal the detector cannot see

Significant literals (strings ≥4 chars, non-trivial numbers) shared across ≥2 modules:

- **requests:** `'utf-8'` in 6 modules (24 occurrences); `'Content-Length'`, `'Proxy-Authorization'`
  (header names) across 3 modules; status codes `500`/`400` hard-coded in `auth`, `models`,
  `status_codes`; `'http'`/`'https'` schemes spread across 3–4 modules. 56 shared literals total.
- **flask:** `'127.0.0.1'` in `app`/`cli`/`testing`; `'OPTIONS'`, `'static'`, `'methods'`,
  `APPLICATION_ROOT`, `FLASK_DEBUG` config keys spread across modules. 70 shared literals total.

These are genuine connascence of meaning — change how the encoding is handled, rename a header, or move
a status code and several modules must agree in lockstep. **The function-structure duplication detector
sees none of them** (they are constants, not function shapes). It maps directly onto the book's worked
example: the loyalty-tier strings (`STANDARD`/`SILVER`/`GOLD`) and a hard-coded discount rate repeated
across checkout, receipt and the revenue report are exactly this signal.

## Result B — locality × degree re-prioritises, and it converges with co-change (P2)

Weighting clusters by locality (same-module=1 < same-package=2 < cross-package=3) × degree surfaces
**cross-package** connascence as the priority:
- requests: 1/8 clusters cross-package (the HTTP verbs, loc3×deg8); the rest same-module (cheap).
- flask: 4/23 cross-package — including `_make_timedelta` (app ↔ sansio/app, loc3).

The convergence with P2 (co-change) is the interesting part:

| flask cluster | connascence locality (P3, structural) | co-change (P2, empirical) | reading |
|---|---|---|---|
| `_make_timedelta` | 3 (cross-package — worst) | 0.94 (lockstep) | **both flag it → strongest consolidation target** |
| HTTP verbs (requests) | 3 (cross-package) | 0.09 (stable) | structural coupling high, but never realised → intentional symmetry, leave |

So connascence is the **structural, a-priori** "would have to change together" and co-change is the
**empirical, a-posteriori** "does change together." Together they discriminate better than either alone:
high on both = genuine accidental copy to DRY; high structural + low empirical = intentional symmetry.

## What the book should take from this

- **Ch.6 + Appendix A:** add **connascence of meaning** (cross-module shared literals/magic values) as
  a drift signal — cheap, deterministic, and orthogonal to duplication and the dependency graph. Each
  with its construct-validity note (it floods; see caveats).
- **Ch.5/Ch.9:** rank consolidation by **locality × degree** — prioritise cross-package, high-degree
  connascence; deprioritise local. Pair with P2 co-change: structural pressure × realised pressure.
- **Vocabulary (Ch.2/Ch.6):** connascence gives a principled name for *why* fragmentation hurts —
  scattered strong connascence at distance — sharper than "duplication."

## Honest caveats
- Connascence of meaning **floods** (56–70 literals on small libraries); many are benign and
  unavoidable (`'utf-8'` everywhere). It is a *surface-to-steward* signal needing ranking/threshold,
  not an auto-gate — same discipline as every detector here. A real version excludes a domain
  allow-list and weights by value rarity.
- Locality is a coarse 1/2/3 proxy; "degree" for meaning is raw occurrence count.
- Part B's algorithm-connascence clusters are the same structural clusters as before, only re-weighted
  — the re-ranking is modest where degree dominates; locality is the discriminating add.
- n = 2 libraries; same Python-AST limits as the other probes.

## Artefacts
- `probe_connascence.py` — connascence-of-meaning detector + locality×degree re-weighting; reuses
  `coherence_ratchet.metrics` internals.

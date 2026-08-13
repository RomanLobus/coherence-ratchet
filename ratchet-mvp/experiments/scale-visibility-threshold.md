# Experiment — the scale/visibility threshold for helper reuse

**Direction:** P7 (emerged from P4). P4's surprise was that agents *reused* the canonical helper in a
tiny package. The program repeatedly names a scale boundary — `retrieval-quality.md`/H1: reuse "fails
at scale past the context window... the failure regime is **named precisely, not demonstrated**"; the
hardening meta-finding calls "too-large-to-see" the genuine open limit. This probe **demonstrates** it.
A canonical `to_cents` helper is buried in a `shop` package of rising size (4 / 42 / 122 modules of
plausible decoys); agents get a neutral task (add an order-total module returning integer cents) with
**no hint a helper exists** — they must discover it. Then a decisive contrast: the same 122-module
package with the helper **renamed to jargon** (`settle.to_minor_units`, so a grep for "cents" misses it).

## Result — reuse collapses with *discoverability*, not size

| Condition | modules | helper name | reuse |
|---|---|---|---|
| small | 4 | `money.to_cents` (lexical match to task word "cents") | **3/3 reuse** |
| medium | 42 | `money.to_cents` | **3/3 reuse** |
| large | 122 | `money.to_cents` | **3/3 reuse** |
| large + jargon (confounded¹) | 122 | `settle.to_minor_units` | **3/3 reinvent** |
| large + jargon (clean) | 122 | `settle.to_minor_units` | **3/3 reinvent** |

**9/9 reuse when the helper is lexically findable — even at 122 modules. 6/6 reinvent when the same
helper, in the same-size package, is named in vocabulary the task does not share.** Size did not move
the needle; the name did. Search-capable agents (they have grep/glob, as real coding agents do)
`grep "cents"`, hit `money.py` even among 122 modules, and reuse. Rename it `to_minor_units` and the
grep returns nothing, so they reinvent a `Decimal` converter — one clean trial even *noticed* `settle.py`
existed and copied its approach rather than importing it.

¹ The confounded jargon dirs inherited a prior run's `order_total.py` with a now-broken `.money` import;
agents reinvented anyway. The clean dirs (no pre-existing file) replicate it, so the result is robust.

## Scope, added 12 August 2026

This result was measured with **search-capable agents**, and its mechanism is a search one: a query
for "cents" hits `money.py` among 122 modules, and returns nothing once the helper is renamed. A
toolless replication of the adjacent question (`scale-visibility-toolless.md`) puts the same
122-module package entirely in context and finds the wall does not appear there: `gpt-5.4-2026-03-05`
reused the canonical helper in 40 of 40 trials whichever name it carried, and
`claude-haiku-4-5-20251001` showed a twenty-five point naming gap that does not clear the
thirty-point rule at n=20.

So this record supports the claim in its retrieval form, that at scale an agent finds what its search
surfaces, and does not support the looser form that agents cannot find helpers in large packages. The
manuscript should cite it for the former only.

## What this demonstrates (and sharpens) for the book

- **The "scale is the open limit" framing is too coarse.** The limit is **retrieval/discoverability**:
  lexical-or-semantic match between the task and the helper, plus a search affordance. Raw module count
  is not the variable — a well-named helper survives 30× growth (4→122) at full reuse; a poorly-named
  one fails at any size. This *demonstrates* what H1 only named.
- **It argues directly for the book's prescribed fix.** Lexical grep is brittle to naming drift; the
  **derived, queryable self-model / catalogue with semantic retrieval** (Ch.3) is exactly what recovers
  the jargon case — surface "the canonical money-to-cents helper" by *concept*, not by hoping the name
  matches. Reframes the scale frontier (Ch.7, Appendix C) as a retrieval-quality problem the method
  already targets, not an unbounded scaling wall.
- **Connects P10:** prevention by surfacing should index helpers by concept, not name.

## Honest caveats
- Agents here have grep/glob and a strong disposition to search — but so do the real coding agents the
  book is about, so this is the realistic regime, not an artefact. An agent with *no* search tool (pure
  in-context generation) would reinvent earlier; that regime is untested here.
- Decoys are generated filler; the helper is a single, clearly-named function; n = 3 per cell.
- The jargon collapse is *lexical*; a semantic/embedding retrieval tool would likely recover it — which
  is the point (it argues for concept-indexed retrieval, the untested upside is P10/retrieval-quality).
- 122 modules still fits a determined agent's search budget; a millions-of-files monorepo where even
  search floods is the next regime up, still untested.

## Artefacts
- `scratchpad/p7/` — fixtures (small/med/large × 3, large-jargon × 3, clean-jargon × 3); `p7_gen.py`.

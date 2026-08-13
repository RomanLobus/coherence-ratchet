# Experiment — Deterministic codemod consolidation

**Why:** the integrator agent (#2) consolidates with an LLM and can silently change behaviour (it altered a rounding mode), needing a behaviour-complete proof. A *deterministic* codemod — an AST transform — could consolidate the safe cases with no behaviour risk at all. This tests where deterministic consolidation works and where it must hand off.

**Result: a deterministic dedupe codemod safely merged exact-duplicate functions (behaviour byte-identical before and after) and correctly refused to touch divergent near-duplicates — establishing the clean division: deterministic codemods for exact/equivalent duplicates (safe by construction, no proof needed), the LLM+proof path for divergent consolidation.**

## What was run
A module with five functions: two exact-duplicate retry loops (`fetch_config`, `fetch_user`), two exact-duplicate cents converters (`price_to_cents`, `refund_to_cents`), and one **divergent** retry (`fetch_user_4tries`, 4 attempts not 3). The codemod groups functions by AST structure (ignoring the name), keeps one canonical per group, and aliases the rest.

| Check | Result |
|---|---|
| Merges performed | `fetch_user → fetch_config`, `refund_to_cents → price_to_cents` (the two exact-duplicate pairs) |
| Divergent `fetch_user_4tries` | **left intact** — 4 tries before and after |
| Behaviour before vs after | **identical** (`fetch_*`→"ok"; cents→1999) |
| Function defs | 5 → 3 (two exact duplicates removed, divergent kept) |

## What it means
- **Deterministic consolidation is safe by construction for exact/structural duplicates.** Aliasing an AST-identical function to its canonical twin cannot change behaviour — there is nothing to get wrong, so no characterisation proof is needed for this class. It is the cheapest, safest paydown available.
- **It correctly refuses the divergent case** — `fetch_user_4tries` differs (4 vs 3 attempts), so it is not AST-equal and the codemod leaves it. That is exactly right: the divergent retries are the case where the integrator agent altered behaviour and needed the proof gate (E4/#2). The codemod's *inability* to touch them is a feature — it stays inside its safe envelope.
- **So consolidation is a two-tier mechanism.** Deterministic codemods sweep the exact/equivalent duplicates with zero risk and zero proof cost; the LLM integrator (behind a behaviour-complete proof, steward-reviewed) handles the divergent cases codemods can't express. Most accumulated duplication in practice is a mix, so both tiers earn their place — and routing the safe cases to the codemod shrinks how much the riskier LLM path has to do.

## Honest caveats
- Only **exact AST-structural** duplicates are in the safe envelope. Functions that are semantically equivalent but textually different (a `for` vs `while` retry) are not caught — they need the semantic detector to *find* and the LLM+proof path to *merge*. The codemod is narrow on purpose.
- Aliasing preserves behaviour but not necessarily intent/readability (two names now point at one function); a real codemod would also rewrite call sites and remove the alias. The behaviour-safety claim is what was tested.
- Toy fixture, Python `ast`; production codemods (e.g. LibCST, Bowler, OpenRewrite) handle imports, call-site rewriting, and formatting — engineering, not research.

## Verdict
A deterministic codemod safely consolidates exact-duplicate functions with no behaviour change and no proof required, and correctly declines divergent ones — giving consolidation a safe, free first tier beneath the LLM integrator. The division of labour: codemods for what is provably equivalent, the proof-gated LLM integrator for what is only semantically equivalent. This narrows the integrator's risky surface to exactly the cases that genuinely need judgment.

→ book: Ch.9 — paydown is two-tier (deterministic codemods for exact duplicates, no proof needed; LLM integrator behind the behaviour-complete proof for divergent ones); route the safe cases to the codemod to shrink the integrator's risk surface. Pairs with #2 (the integrator) and E4 (the proof requirement).

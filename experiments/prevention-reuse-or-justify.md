# Experiment E1 — Prevention at authoring time (reuse-or-justify / surfacing)

**Hypothesis:** forcing an agent to reuse-or-justify against the system's existing abstractions cuts fragmentation at the source.

**Result: the hypothesis is right, but the lever is not the one assumed.** The additive/reinvention bias is overwhelmingly a **retrieval/visibility** problem, not a willingness problem. Agents reuse a helper they can see and reinvent one they can't — and a "reuse-or-justify" instruction adds nothing once the helper is already in context.

## Two probes (10 trials per condition, Claude judges, low effort)

**E1 — helper visible in context.** Both conditions were shown the canonical `retry` helper; the treatment added a sanctioned-helpers catalogue + a reuse-or-justify rule.

| Condition | Reuse rate |
|---|---|
| control (helper visible, no instruction) | **10/10** |
| treatment (helper visible, catalogue + reuse-or-justify) | **10/10** |
| lift | **0.00** |

**E1b — helper NOT visible in context.** Control was shown a billing package with `retry.py` *omitted*; treatment added a catalogue entry that *surfaced* the existing helper.

| Condition | Reuse rate |
|---|---|
| control (helper not surfaced) | **0/10** — all ten reinvented their own retry loop |
| treatment (catalogue surfaces the helper) | **10/10** — all ten imported and reused it |
| lift | **1.00** |

## What it means

- **Visibility, not exhortation, is the lever.** When the helper was in context, reuse was 100% regardless of instruction. When it wasn't, agents reinvented 100% of the time — and simply *surfacing* it flipped them to 100% reuse. The "reuse-or-justify" wording was not what mattered; getting the abstraction in front of the agent was.
- **This explains R3 mechanistically.** Agents "build against the task, not the system" not because they refuse to reuse, but because the system is not in their context window. Fix retrieval and you fix the bias for the cases where the right abstraction exists and is surfaced.
- **It upgrades the catalogue from a detection reference to a prevention mechanism.** The same human-curated catalogue that the gate matches against, surfaced at *authoring* time, prevents the divergence the gate would otherwise have to catch downstream. One artefact, two jobs — and prevention is cheaper than detection-plus-consolidation.
- **It makes the method less reactive.** Prevention (surface the relevant catalogue entries at authoring) should run *first*; the deterministic detector and gate become the backstop for what slips through.

## Honest caveats (the result is suspiciously clean for a reason)
- **Toy 1:1 mapping.** The task maps cleanly to exactly one helper, so reuse is binary and the rates hit 0%/100%. Real tasks are fuzzier; the rates will not be that extreme.
- **The new hard problem is retrieval/ranking.** "Surface the relevant helper" presumes you know *which* of hundreds of catalogue entries is relevant to this change. With a real catalogue you cannot surface everything (context limits), so the prevention lever's effectiveness becomes a *retrieval-quality* problem — which the book must name, and which is an open engineering question.
- **Claude-only, n=10, single helper, structural classification** (reuse detected by a `retry(` call vs an own loop). Suggestive, not conclusive.
- The instruction may still matter in the fuzzy middle (when a helper *partially* fits) — untested here.

## Verdict
Prevention works, and the experiment identifies its real lever: **retrieval/surfacing of the sanctioned abstraction at authoring time**, not the reuse-or-justify wording. This is the strongest actionable solution finding so far — it gives the method a cheap prevention front end and reframes the catalogue as a prevention mechanism, not only a detection reference. The honest sequel is that it converts the problem into a retrieval-quality problem ("surface the *right* entry"), which the book should pose as the next open question.

→ book: a prevention layer in Ch.3/Ch.7; the catalogue's dual role; the retrieval-quality open problem in the "beyond the ratchet" chapter.

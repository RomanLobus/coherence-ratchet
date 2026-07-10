# Experiment H4 — Design-memory decay over a long sequence

**Hypothesis (defends/extends E3):** E3 showed a design-memory note eliminated reinvention over ~5 tasks (n=1). R4 warns that every curated artefact rots by accretion. Over a longer sequence, does the self-maintained note bloat, and does reuse degrade as it does? A pruned (size-budgeted) arm tests whether a budget fixes it.

**Result: three findings, one of them a sharp correction to E3.** A design-memory *note* drives reuse only when it points to code the agent can actually import; the unpruned note accretes ~10× over 15 tasks; and a size budget bounds it at zero cost to reuse. Reuse did not degrade within 15 tasks even when the note bloated.

Setup: 15 sequential billing tasks across four recurring concepts (retry, to-cents, paginate, validate-email), so 11 are reuse opportunities. One agent per step carries a running design-memory note (it never sees prior code directly). Two arms — unpruned, and pruned (note kept under 120 words).

## Finding 1 — a note must point to importable code, not merely describe it (the E3 correction)
The first run (H4) told the agent it *could not see prior code — only the note*. Reuse collapsed:

| Arm (note-only) | Reused an existing helper | Note growth |
|---|---|---|
| unpruned | **2/11** | 56 → 261 words |
| pruned | **3/11** | bounded ≤ 84 |

The agent re-defined `dollars_to_cents` again and again *despite it being in the note*, because it could not import what it could not see — to produce runnable task code it rewrote the helper. So a note that merely **describes** established helpers does not drive reuse.

The corrected run (H4b) told the agent those helpers live in an importable `helpers.py`. Reuse jumped:

| Arm (import allowed) | Reused | Reinvented on a reuse-opp task | Late-sequence reuse |
|---|---|---|---|
| unpruned | **10/11** | 1/11 | 7/8 |
| pruned | **11/11** | **0/11** | **8/8** |

This is the E1b lesson again, across time: the lever is surfacing the **real callable abstraction**, not prose about it. Design memory works when it is a *pointer to reusable code*; it fails when it is a *description* of code the agent cannot reach. E3's clean result holds — but only under the importable condition E3 happened to use; it does not generalise to note-as-description.

## Finding 2 — the unpruned note accretes (~10×), confirming R4 for design memory
In H4b the unpruned note grew 34 → 343 words over the sequence (climbing almost monotonically to task 14 before the agent finally dumped it). That is the accretion R4 measured for comments, docs, and agent context files, reproduced for a self-maintained design-memory note: left unmanaged, it grows by addition.

## Finding 3 — a size budget bounds the note at no cost to reuse
The pruned arm stayed under 74 words throughout and achieved **perfect reuse (11/11, late 8/8)** — slightly better than unpruned (10/11, one reinvention). So a pruning budget is a free win: it keeps the memory small *and* keeps reuse maximal. This ties design memory to the catalogue's anti-staleness engineering (R4): both need pruning, and both need code-tying (the note's entries must map to importable code, exactly as the catalogue's entries map to code exemplars).

## Honest caveats
- **Reuse did not degrade within 15 tasks, even at 343-word bloat.** So the decay risk is *real* (the note bloats) but had not yet defeated reuse at this length — the breaking point, where bloat actually causes the agent to lose the helper, is beyond 15 tasks and untested. The result shows accretion happens and pruning is costless, not that bloat is harmful within this horizon.
- `reused`/`created` are the agent's structured self-report; the note word-counts and the reuse-vs-reinvent direction are corroborated by the recurring `created: dollars_to_cents` pattern in H4, but this is not an execution-level reuse check.
- Claude-only, Python, n=1 sequence per arm (the per-step agents are independent, but the sequence itself is single-run). A multi-sequence version would turn these into rates.

## Verdict
Design memory works over a long sequence — 10–11/11 reuse, no late-sequence degradation — but only as a **pointer to importable code**, not as a description (note-only reuse was 2–3/11). The unpruned note accretes ~10× (R4 confirmed for this artefact), and a size budget bounds it with no reuse penalty (pruned beat unpruned, 11/11 vs 10/11). The honest upgrade to E3: keep the memory, but engineer it like the catalogue — code-tied (importable) and pruned — or it rots the same way every other curated artefact does.

→ book: Ch.3 (design memory) gains two engineering requirements — it must point to importable code and it must be pruned — unifying it with the catalogue's anti-staleness discipline (R4). E3's headline holds with these caveats. New dead-end nuance: "a design-memory note that *describes* helpers is enough" — refuted (2–3/11); it must surface the callable abstraction. Logged future work: find the sequence length / note size at which bloat actually defeats reuse.

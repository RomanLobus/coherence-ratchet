# Experiment E3 — Does design memory reduce reinvention?

**Hypothesis (R3's open question):** giving an agent persistent design memory across a task sequence reduces the additive/reinvention bias. The literature has not measured this.

**Result: a clean demonstration that it does.** The same five related tasks, built two ways, then measured with the MVP detector:

| Condition | Functions | Redundant clusters | Duplication ratio |
|---|---|---|---|
| No memory (5 independent agents, no shared context) | 8 | 2 | **0.62** |
| Memory (one agent carrying a running design-memory note) | 6 | 0 | **0.00** |

- **No memory** reinvented relentlessly: three separate `to_cents` implementations, two divergent retry loops (one agent even redefined its own `TransientError` class). The shared capabilities (retry, money conversion, pagination) were rebuilt per task.
- **Memory** established each capability once — `retry_on_transient`, `to_cents`, `paginate` in `billing/helpers.py` — and every later task imported and reused it. No duplication at all.

## What it means

- **Persistent design memory measurably eliminates reinvention here.** This is the first-party answer to R3's unstudied question: the "agents have no cross-session memory" cause is not just plausible, it is *operative* — remove the memory and redundancy appears, restore it and redundancy vanishes.
- **Memory is "surfacing, accumulated over a session."** It is the same lever E1/E1b found (agents reuse what they can see), extended across time: a running note of established abstractions keeps the system in the agent's context as the session grows. The agent even maintained the note correctly without prompting errors — establishing three helpers and reusing them across the remaining tasks.
- **Together with E1/E1b, the prevention story is coherent:** fragmentation is a *context* problem (the system isn't in front of the agent), and both retrieval (E1b) and accumulated memory (E3) fix it by putting it there.

## Honest caveats (important)
- **n = 1 per condition.** This is a single demonstration sequence, not a multi-trial rate. The 0.62 → 0.00 delta is clean and the mechanism is clear, but a robust result needs several independent sequences. (E1b's surfacing mechanism *was* multi-trial at n=10, which is what gives this confidence; E3 shows the accumulation works end-to-end.)
- **No-memory was deliberately isolated** (each agent saw no sibling code) to model "no cross-session memory." Real agents with repo tools might find some helpers, so this is the upper-bound effect.
- **Self-maintained memory worked here**, but R4 warns curated artefacts rot by accretion — a real design memory needs the same anti-staleness engineering (pruning, code-tying) as the catalogue. This experiment did not run long enough to hit that.
- Claude-only, Python, toy tasks with clean shared capabilities.

## Verdict
Design memory works as a reinvention-reducer in this demonstration, and converges with the prevention finding: keep the system's established abstractions in the agent's context — by retrieval (E1b) or accumulated memory (E3) — and the additive bias largely disappears. The honest next step is a multi-trial version and a longer sequence to see whether the self-maintained note itself decays (R4's accretion risk).

→ book: design memory as a first-class artefact (Ch.3), the "fragmentation is a context problem" framing (Ch.2/Ch.7), and the convergence of prevention + memory + catalogue as one mechanism (surface the system to the agent). Multi-trial + decay test logged as future work.

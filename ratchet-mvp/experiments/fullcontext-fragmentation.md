# Experiment — does more context fix fragmentation, or does surfacing?

**Direction:** the demand-side threat "AI will fix this itself — bigger context windows and better models
will just reuse what's already there." This probe tests it head-on. A billing subsystem already contains
two clearly-canonical helpers (`billing.money.to_cents`, `billing.retry.retry`). A coding agent is asked
to write a new function that needs both, under four context conditions (3 trials each, Claude subagents,
no tools, deterministic reuse/reinvent scorer in `probe_fullcontext_fragmentation.py`).

## Result — at subsystem scale, context fixes it; only absence forces reinvention

| condition | what the agent saw | reuse | reinvent |
|---|---|---:|---:|
| **task-only** | the task only; the helper not in context at all | **0/3** | **3/3** |
| **full-context** | the whole subsystem source | **3/3** | 0/3 |
| **full-surfaced** | whole subsystem + a self-model line naming the canonical helpers | **3/3** | 0/3 |
| **full-buried** | whole subsystem, but the helpers renamed to jargon (`_q`, `_attempt`), no "cents"/"retry" cues, among noise modules | **3/3** | 0/3 |

The task-only agents each wrote their own `Decimal`-based cents conversion and their own retry loop — the
familiar reinvention default. But every agent that had the subsystem **in context reused the helper** —
including the buried condition, where the helpers were named `_q` and `_attempt` with docstrings that
never said "cents" or "retry". The models read `"""Normalise a value to its minor-unit integer
representation"""` and `"""Run fn a few times, tolerating hiccups"""`, matched them to the task, and
imported them. Reinvention appeared **only** when the helper was not in the context at all.

## What it means — and it is partly inconvenient for the book

This is an honest, calibrated result, and it tempers a naive version of the book's own argument.

- **"More context fixes fragmentation" holds at subsystem scale.** A capable model with the relevant code
  in its window reuses what is there, even under adversarial naming. So the threat-1 answer **cannot** rest
  on "agents can't find or reuse existing helpers" — at this scale they can, reliably, by reading the code.
  This replicates the RES2/RES2b diligence pattern from the Residuality pass (agents found buried and
  divergent sites when they could see them) rather than contradicting it.

- **The reinvention default is a *context* problem, not a capability one.** The only condition that produced
  reinvention was the one where the helper was outside the model's context. That is the whole game: the
  question is not whether a model reuses what it sees, but whether the thing it needs is *in what it sees*.

So the persistence of coherence decay under AI — the real answer to "AI will fix it" — rests on the four
places this toy, single-task, small-subsystem probe deliberately does not reach:

1. **Scale / discoverability.** At subsystem size, full context *is* discoverability. At repository scale it
   is not: P7 (`scale-visibility-threshold`) showed the same jargon-renamed helper reinvented 6/6 at 122
   modules, because it could no longer be surfaced. Context windows help until the relevant helper cannot be
   found in the noise — which is the common real case, not the toy one.
2. **Relocation beyond context.** The fragmentation that matters is the coherence that does *not* fit one
   window — cross-file, cross-service, architectural (`reframe-Eb-beyond-context`; the architecture-decay
   curve, where function-duplication fell while cycles rose 0→0.83). A bigger window that still isn't the
   whole system does not see it.
3. **Cross-agent, cross-session fragmentation + the untouched consolidation term.** One well-contexted task
   reuses; five independent agents each with their own context still fragmented a codebase to 0.80
   duplication (`integrator-agent`), and none of them proactively *consolidated* the divergence that already
   existed. Reuse-when-you-see-it does not remove decay; something must still do the consolidating.
4. **The enabler case, strengthened.** Surfacing drove reuse from 0/3 to 3/3. That is the positive form of
   the argument: the derived self-model exists precisely to *guarantee* the relevant shape is in the agent's
   context at scale and across agents — the thing that, in this probe, made reuse automatic. The method is
   what turns "reuses if it happens to see it" into "reliably sees it".

## Honest limits

- n = 3 per condition, Claude subagents, one toy fixture, no tools. Small scale is exactly the regime where
  full context equals discoverability, so this probe **cannot** speak to the scale collapse — that is P7's
  regime, and P7 is the load-bearing evidence for the scale claim, not this.
- The scorer is deterministic (word-boundary reuse detection vs own-conversion / own-loop reinvention),
  validated on known reuse and reinvent samples.
- A single model family; a diligent model is assumed (real coding agents are). A weaker model might reinvent
  even in context — untested.

## Verdict

The probe answers "AI will fix it" precisely, not conveniently: **yes, at subsystem scale, a capable model
reuses what is in its context — so the book must not claim otherwise.** The decay persists because of scale
and discoverability, coherence that lives beyond any one context window, and fragmentation spread across
independent agents that no one consolidates — and because surfacing is what drives reuse, the derived
self-model is the mechanism that makes reuse reliable rather than incidental. This sharpens Ch.2 beat 2.5
("why capability does not fix it" → *capability plus full context does fix a single scoped task; what it does
not fix is the at-scale, beyond-context, cross-agent regime and the consolidation term*) and directly
supports the enabler reframe (Ch.1/9/11/12).
→ book: Ch.2 (sharpen 2.5 with this evidence), Ch.1/12 (the enabler reframe), Appendix C. [Claim 45]

## Replication, 12 August 2026 — n=10, pinned model, committed artefacts

The original run above was three trials per condition against unpinned "Claude subagents", with the
prompts and returned code living in a session scratchpad. It has been re-run through the committed
harness (`experiments/harness/`), which dispatches the probe's own `build_prompt` to a dated model
snapshot, persists every raw response, and scores them with the probe's own deterministic scorer.

| condition | n | reuse (both helpers) | reinvention |
|---|---:|---:|---:|
| `task_only` | 10 | **0/10** | 10/10 |
| `full_context` | 10 | **10/10** | 0/10 |
| `full_surfaced` | 10 | **10/10** | 0/10 |
| `full_buried` | 10 | **10/10** | 0/10 |

Model `claude-haiku-4-5-20251001`, temperature 1.0, 10 trials per condition, no trial
errors. Run directory `experiments/data/runs/fullcontext/2026-08-12-haiku-4-5`, with `manifest.json` carrying the probe hash, the per-condition prompt
hashes, and the run dates.

**The result replicates exactly.** Reinvention appeared only where the helper was outside the context;
every condition that carried the subsystem produced reuse in all ten trials, including the buried
condition where the helpers are named `_q` and `_attempt` and no docstring says "cents" or "retry".
Raising n from three to ten changed nothing, which is the outcome a ceiling effect predicts: at this
fixture size there is no room between conditions for a difference to appear.

Two consequences follow, and the second is the one that matters for the manuscript.

The finding is now checkable rather than recorded. The raw responses are committed, so the scoring can
be disputed offline by a reader with no API key, and `dispatch.py --verify` reports whether the probe
or its prompts have moved since the run. The class letter changes accordingly.

And the ceiling is now measured rather than asserted. This probe cannot discriminate between full
context and surfacing, because at subsystem scale both reach 10/10, so it may not be cited for the
claim that surfacing beats context. It carries the floor result, that absence forces reinvention, and
nothing above it. The scale claim rests on `scale-visibility-threshold.md`, where the same jargon-named
helper was reinvented 6/6 at 122 modules, and the beyond-context claim rests on
`reframe-Eb-beyond-context.md`. Any manuscript sentence that reaches past the floor result needs one of
those two as its citation.

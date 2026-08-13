# Experiment R3b — does lexical mismatch hide a helper at scale when the agent has no tools?

**Direction:** `scale-visibility-threshold.md` is the load-bearing evidence for the book's scale
claim, and `fullcontext-fragmentation.md`'s replication made it more load-bearing rather than less: at
subsystem scale every in-context condition reaches 10/10 reuse, so that probe cannot carry the claim
and R3 must. R3 sits at 9/9 and 6/6 on one model family, and its agents had grep and glob. Its
mechanism is explicitly a search one: a query for "cents" hits `money.py` even among 122 modules, and
returns nothing once the helper is renamed `settle.to_minor_units`.

This harness dispatches a single API call with no tools, so that regime cannot be replicated here and
this probe does not claim to replicate it. It runs the adjacent question, which the earlier probe
leaves open: with the whole package **in context** and no search available, does a package of 122
modules plus a lexical mismatch defeat reuse? At five modules it did not — `full_buried` reached 10/10
with the helper renamed to jargon. Twenty-five times the modules is the obvious next size.

## Setup

Two conditions, identical but for the helper's name and its docstring vocabulary, both carrying all
122 modules in context (about 7,300 tokens):

    match    shop/money.py    to_cents(amount)        docstring says "integer number of cents"
    jargon   shop/settle.py   to_minor_units(value)   docstring says "smallest indivisible denomination"

The 121 decoy modules are generated from a fixed seed, so the package is byte-identical across trials,
conditions, vendors and re-runs, and the helper sits at the same index in both conditions so position
is held constant. The task asks for an order-total module returning integer cents, with no hint that a
helper exists. Twenty trials per condition per family.

## Result — no separation at this sample in one family, and no effect at all in the other

| family | condition | n | reuse | rate | 95% CI |
|---|---|---:|---:|---:|---|
| `claude-haiku-4-5-20251001` | match | 20 | 16 | 0.80 | [0.58, 0.92] |
| `claude-haiku-4-5-20251001` | jargon | 20 | 11 | 0.55 | [0.34, 0.74] |
| `gpt-5.4-2026-03-05` | match | 20 | 20 | 1.00 | [0.84, 1.00] |
| `gpt-5.4-2026-03-05` | jargon | 20 | 20 | 1.00 | [0.84, 1.00] |

**The naming effect is reported as no separation at this sample.** The pre-declared rule in Appendix C
is that a pair of cells separated by fewer than thirty percentage points at n=20 is reported as no
separation rather than as a result. The `haiku` gap is twenty-five points and the intervals overlap,
so it does not clear the bar. Publishing it as a finding would be exactly the practice the rule exists
to prevent, and the rule was written before this run.

**In the frontier family there is no effect to report at all.** Forty trials out of forty reused the
canonical helper, whether it was called `to_cents` or `to_minor_units`. Scale did not hide it and
vocabulary did not hide it.

**What did move, in one family, is reuse under scale itself.** At five modules `fullcontext`'s buried
condition reached 10/10 for the same model family. At 122 modules the matching-name condition reaches
16/20 and the jargon condition 11/20. Both are below the small-package ceiling, and the direction is
consistent with the book's argument even where the naming contrast is not resolvable at this sample.

## What it means, including what it costs the argument

**The toolless regime does not reproduce the discoverability wall.** R3's result stands where it was
measured, with search-capable agents, and its mechanism is about what a query returns. This run shows
that mechanism does not transfer to an agent that has the package in its context window and no search:
a frontier model reads 122 modules and finds a jargon-named helper every time.

**The manuscript must therefore attribute the scale claim precisely.** The claim is safe in the form
R3 measured it, which is about retrieval: at scale, an agent finds what its search surfaces, and a
helper named in vocabulary the task does not share is not surfaced. It is not safe in the looser form
that agents cannot find helpers in large packages. Any sentence resting on the looser form is
contradicted by forty trials here.

**And the honest reading of the whole set is narrower than the programme's earlier framing.** Across
`fullcontext`, `no-chokepoint` and this probe, the condition that reliably produces reinvention is not
size and not naming. It is **absence**: the helper outside the context window, or the second site
never named. Both of those the derived model addresses directly, which is the argument the book should
make, and it is a smaller argument than "context windows will not save you".

## Honest limits

- Twenty trials per condition per family, two families, one fixture, one task. The rule applied above
  is a floor on what may be claimed, not a claim that no effect exists; a larger n might resolve the
  twenty-five point gap in either direction.
- The decoys are synthetic and regular in shape. A real 122-module package is more varied and probably
  harder to read, so this is a favourable case for the model.
- One task, one helper. The task's wording shares vocabulary with the matching condition by
  construction, which is the manipulation; a task worded neutrally against both would be a cleaner
  three-way design and was not run.
- Both families here are current tiers. Nothing is claimed about older or smaller models, and the
  gap between the two families in this run is itself a reason not to generalise across tiers.

## Reproduce

    python3 experiments/harness/dispatch.py --probe probe_scale_visibility.py \
        --trials 20 --model claude-haiku-4-5-20251001 \
        --out experiments/data/runs/scale/2026-08-12-haiku-4-5
    python3 probe_scale_visibility.py --tally experiments/data/runs/scale/2026-08-12-haiku-4-5

Raw responses and manifests are committed for both families. Scoring re-runs offline with `--rescore`
and needs no API key.

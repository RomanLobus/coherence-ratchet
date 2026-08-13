# The coherence ratchet — reference implementation

This is the **reference implementation** for the book *Coherence Debt: Keeping
Software Worth Changing When AI Writes the Code*. It is an existence proof that
the book's method is buildable and runnable, and it is deliberately minimal. It
is a companion to the book, **not a product to adopt in place of the method**:
it shows the *shape* of the answer and lets a team try the ideas on real code.
The theory, the operating model, the judgement calls, and the at-scale story
live in the book. Run it to see the ideas work, then read the book to know what
to do.

It exists to make one claim checkable: **design-coherence decay under
AI-authored change is measurable, and a ratchet can hold it.**

The method is one loop of seven stations:

> derive → ratify → ground → author → detect → hold → judge

The deterministic floor needs no LLM, no network, and no dependency beyond the
Python standard library. The semantic layer is optional, env-gated, and never
acts on its own.

## What it shows

Run `python3 ratchet-mvp/demo.py`. A tiny billing subsystem starts coherent (one retry
helper, one paginator), then an AI-style author adds three features, each
quietly re-implementing retry instead of reusing it. The redundancy curve
climbs, the ratchet trips on every decay commit, and a consolidation pass that
reuses the canonical helpers brings the curve back to zero:

```
  commit             clusters  dup-ratio
  00-baseline               0       0.00
  01-orders                 1       0.40    <- orders.py reinvents retry
  02-exports                2       0.71    <- exports.py reinvents retry + paginate
  03-loyalty                2       0.75    <- loyalty.py reinvents retry again
  04-consolidated           0       0.00    <- copies reuse the canonical helpers
```

`QUICKSTART.md` walks one honest pass through the whole loop on the
checkout-pricing fixture, and every command in it runs offline.

## Four kinds of truth

The distinction the rest of the tool is built on: what the code demonstrably
contains is not what a team has authorised, and only the authorised part may
instruct an agent.

`selfmodel derive` writes `coherence/selfmodel.json`, recording the source
revision and tree hash, the extractor identity and ruleset hash, mechanically
observed structure, and heuristic candidates. Frequency does not confer
authority: a pattern repeated fifty times is still only a candidate.

A human-owned `coherence/intent.json` records ratified contracts and
conventions with approver, date, rationale, scope, exceptions, and the hash of
the model they were ratified against. `selfmodel ratify` is the only path from
candidate to ratified intent.

Queries and grounding packs label every statement `[OBSERVED]`, `[CANDIDATE]`,
or `[RATIFIED]`. Only the last may issue an imperative. `selfmodel context`
re-derives the source and refuses to render when the saved model is stale or
the intent hash does not match.

## Grounding: putting ratified intent where agents read it

`ground` writes the ratified subset into the files coding agents actually read
(`AGENTS.md` by default; `CLAUDE.md`, `.cursorrules` and
`.github/copilot-instructions.md` are also known targets), and `ground --check`
fails when the committed block no longer matches a fresh derivation. That is
the answer to hand-maintained architecture documents going stale: the artefact
is derived, and the build notices when it stops describing the code.

```sh
P=ratchet-mvp/playground/_states/06-checkout-cycle/checkout_pricing
coherence-ratchet ground "$P" --model coherence/selfmodel.json --intent coherence/intent.json
coherence-ratchet ground "$P" --check --model coherence/selfmodel.json --intent coherence/intent.json
```

This is the station the book leans on hardest, and the experiment record is in
the repository rather than only summarised. In `ratchet-mvp/experiments/no-chokepoint.md`,
agents making a cross-cutting change to a system whose second total-computation
site sat outside their context got it right **0 times out of 30**; the same
agents given the derived pack got it right **30 out of 30**, replicated on a
second vendor's model. Two controls sit beside it: telling an agent to reuse
what it can already see moves reuse by nothing, and a fabricated pack naming
helpers that do not exist is ignored when the agent can read the code and
followed when it cannot. The write-up states the models, dates, trial counts,
confidence intervals, and limits, including a scoring defect that was found,
corrected, and disclosed because it moved a printed number.

`advise` measures a staged change against the existing code and returns a
revision instruction; `serve` exposes ratified intent to agents over MCP.

## Ratchet semantics

`init` captures the current baseline, so the tool starts from today's tangle
rather than demanding a cleanup first. An unchanged `check` passes. A check
trips only when a watched signal worsens past its ceiling.

The ratchet watches a **portfolio** — duplication, dependency cycles, and
connascence of shared literals — because a fragmenting change can slip past any
single measure. Coupling, fan-in, hyperliminal pairs and contagion are reported
as diagnostics beside it and never ratcheted: raw coupling is not
lower-is-better, since consolidation legitimately raises coupling to a shared
helper.

Improvement can lower a ceiling with `--tighten`, which records who lowered it.
A pawl refuses to lower a ceiling whose raw numerator did not also fall, so a
growing codebase cannot dilute its way to a tighter-looking ratio.

Accepted deterioration is not a flag. It requires an owner, a repayment
trigger, a review date, evidence, confidence, all five exposure dimensions, and
repayment feasibility, or an explicit `--needs-assessment`:

```sh
coherence-ratchet init  ratchet-mvp/playground/_states/00-baseline/billing --budgets /tmp/b.json \
    --by "you" --reason "first baseline"
coherence-ratchet check ratchet-mvp/playground/_states/03-loyalty/billing  --budgets /tmp/b.json   # exits 1
coherence-ratchet check ratchet-mvp/playground/_states/03-loyalty/billing  --budgets /tmp/b.json \
    --accept --owner billing-team --trigger "next settlement refactor" \
    --volatility medium --coordination-span low --criticality medium \
    --discoverability low --blast-radius low \
    --evidence "REPRODUCIBLE_FIXTURE: ratchet-mvp/playground/_states/03-loyalty" \
    --confidence medium --review-date 2027-01-01 --repayment-feasibility medium \
    --ledger /tmp/ledger.jsonl
```

`history` samples the portfolio across committed revisions through
`git archive`, without touching the working tree or HEAD.

## Exposure, not price

Ledger entries assess five ordinal dimensions as `low`, `medium` or `high`:
volatility, coordination span, criticality, discoverability, and blast radius.
Missing evidence yields `NEEDS_ASSESSMENT`; complete records resolve to `LOW`,
`MODERATE` or `HIGH`. Repayment feasibility is recorded separately. **There is
no summed score and no currency estimate.** A single number would invite a
false trade against delivery, and the dimensions do not commensurate.

`report` reads the ledger and prints leading indicators a team can stand
behind: coverage, open items by region, overdue items, and how long the ratchet
has held. These are process indicators, not savings.

## Verification vocabulary

`compare` performs bounded differential testing of a consolidation against the
original, over an adversarial seed library aimed at the change points plus
type-driven generation, comparing return values and raised-exception types.

Its terminal statuses are `REFUTED` (a counterexample was found),
`NO_DIVERGENCE_FOUND` (no difference appeared in the stated tested space), and
`UNPROVEN` (the case was unsupported or inconclusive). **There is no `PROVED`.**
The absence of a counterexample in a bounded space is not a proof, and the tool
declines to print a word that would let it be read as one.

```sh
F=ratchet-mvp/_fixtures/consolidation
coherence-ratchet compare "$F::variants.to_cents_half_up" "$F::variants.to_cents_half_even"
coherence-ratchet compare "$F::variants.retry_orig" "$F::variants.retry_faithful" \
    --strategy "$F/retry_strategy.py"
```

`apidiff` is separate evidence, and deliberately so: it diffs the public API
surface of two trees and reports removed symbols, removed or renamed
caller-passable parameters, new required parameters, and dropped defaults. A
changed default *value* is a behaviour change that `compare` refutes and
`apidiff` will not, which is the clearest illustration of why the two are not
one check.

Side effects, non-determinism, environmental assumptions, and whether the
intended semantics are correct remain human review.

## The optional semantic gate

The deterministic floor flags duplicate clusters but cannot tell *sanctioned*
symmetry from *uncatalogued* fragmentation. `gate` adds the LLM layer over the
deterministic residue, asking it to match a specific pattern in the ratified
catalogue or return NONE — multi-trial, with a conservative quorum to clear.
Anything short surfaces to a steward.

```sh
coherence-ratchet gate ratchet-mvp/playground/_states/03-loyalty/billing \
    --catalogue ratchet-mvp/coherence/catalogue.example.json \
    --layering  ratchet-mvp/coherence/layering.example.json
```

It is env-gated on `ANTHROPIC_API_KEY`. With no key it prints a clean
"skipped", the deterministic layering check still runs, and the `check` CI gate
is untouched. With no catalogue it surfaces all duplication, which is the safe
default. It clears only what a steward has ratified, and never auto-acts.

`calibrate` samples function pairs for hand labelling and reports the threshold
curve, because the similarity threshold shipped here was tuned against these
fixtures and a real codebase needs its own.

## Run it

```sh
git clone https://github.com/RomanLobus/coherence-ratchet
cd coherence-ratchet
pip install ./ratchet-mvp   # installs the `coherence-ratchet` command
python3 ratchet-mvp/demo.py             # the curve and the ratchet decisions
python3 ratchet-mvp/tests/run.py        # 201 tests, offline
```

Then follow `QUICKSTART.md` for one pass through the whole loop.
Without installing, prefix any command with `python3 -m coherence_ratchet …`.

## What it deliberately leaves out, and why

- **The LLM layers are optional and off by default.** The controlled
  experiments found an LLM confidently wrong as an autonomous judge of what
  should consolidate. The only framing that survived is objective matching
  against a human-ratified catalogue, surfacing to a steward.
- **No consolidation engine.** The tool refuses a bad merge; it does not
  perform the merge. Performing it stays with the team or its agent, behind the
  comparison.
- **Coupling is reported, not ratcheted**, for the reason given above.
- **The similarity threshold is calibrated against these fixtures**
  (`MIN_TOKENS = 12`, `SHINGLE_K = 5`, `SIM_THRESHOLD = 0.45`). A real codebase
  needs its own calibration; `calibrate` is how to get it.
- **Martin's main-sequence distance was measured and retired for Python.**
  Across four mature libraries, abstractness sat at roughly zero, so the metric
  collapsed to a restatement of instability and drifted *healthier* while cycles
  climbed. The negative result is kept rather than quietly dropped.
- **O(n²) pairwise comparison.** Fine for a playground; a real tool needs LSH
  or MinHash bucketing.

## Reproducibility

Output formats are frozen per minor version, and `ratchet-mvp/CHANGELOG.md` records every
change to a printed format, so a reader who finds the tool disagreeing with a
printed block in the book can tell a version gap from a defect. **This release
is 0.5.0, and it is the version the book's printed blocks are pinned to.**

The longitudinal readings are pinned to named commits rather than re-sampled:
`ratchet-mvp/experiments/` holds the write-ups and `ratchet-mvp/experiments/data/` the measured output
for each library, stamped with the analyser version and hash. Even-index
sampling over a growing history is epoch-dependent, so the pins are what make
the printed digits reproducible.

`ratchet-mvp/experiments/README.md` is the per-claim index, and classifies each write-up by
whether it is re-runnable from a script, re-runnable as an LLM probe, or a
recorded run only.

## Licence

MIT. See `LICENSE`.

# The coherence ratchet — reference implementation

This is the **reference implementation** for the book *Coherence Debt: Keeping
Software Worth Changing When AI Writes the Code* — an existence proof that its
method is buildable and runnable, deliberately a minimal MVP. It is a companion
to the book, **not a product to adopt in place of the method**: it shows the
*shape* of the answer and lets a team try the ideas on real code; the answer —
the theory, the operating model, the judgement calls, and the at-scale story —
lives in the book. Run it to see the ideas work, then read the book to know
what to do.

It is a runnable proof of one claim from the book: **design-coherence decay
under AI-authored change is measurable, and a ratchet can hold it.**

This MVP is deliberately the *deterministic floor* of the method. No LLM, no
network, no dependencies beyond the Python standard library. It measures how
often the same idea gets re-implemented instead of reused, treats that number
the way a coverage ratchet treats coverage — it may hold or fall, never rise —
and records every breach somebody chooses to accept.

## What it proves

Run `python3 demo.py`. A tiny billing subsystem starts coherent (one retry
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

That rising-then-falling curve is the empirical artefact the field does not yet
have, produced here from the AST with an exact, reproducible measurement.

## Tried on real repositories

Measured against three well-known public Python projects (package source only,
dunders excluded), each in well under a second:

| Repo | Functions | Redundancy clusters | Duplication ratio |
|------|-----------|---------------------|-------------------|
| psf/requests | 159 | 8 | 0.16 |
| pallets/flask | 261 | 23 | 0.26 |
| httpie/cli | 320 | 9 | 0.06 |

Three things this taught, all of which sharpen the method:

1. **The signal is real and codebase-specific** (0.06–0.26), not a constant.
   In `requests`, `auth.md5_utf8 / sha_utf8 / sha256_utf8 / sha512_utf8` is a true
   consolidation candidate — four copies of one idea differing only by hash
   function.
2. **It also flags deliberate repetition.** The `requests` public API
   (`get/post/put/options/head/patch`, each `return request("verb", …)`) is
   intentional symmetry, not decay. Raw redundancy mixes genuine duplication,
   intentional symmetry, and protocol boilerplate. Dunder methods are excluded
   for this reason; decorator wrappers (`wrapper`/`wrapped`) are the next
   obvious exclusion. Sanctioned patterns belong in the pattern catalogue, and
   separating decay from deliberate symmetry is exactly the job the semantic
   gate exists to do.
3. **The ratchet is a *delta* instrument, not an absolute score.** You do not
   tell `requests` to fix its 0.16; you baseline it and forbid backsliding —
   the way a coverage ratchet does not demand 100%. Confirmed directly:
   `init` on `requests` then `check` against itself reports "coherence held."

Reproduce:

```sh
git clone --depth 1 https://github.com/psf/requests /tmp/requests
python3 -m coherence_ratchet measure /tmp/requests/src/requests
```

## How it works

- **`coherence_ratchet/metrics.py`** — parses the tree and finds clusters of
  near-duplicate functions (a structure-preserving token signature, k-gram
  shingling, Jaccard similarity, union-find). The headline metric is
  *redundant functions / clusters*: the same idea built more than once.
- **`coherence_ratchet/archmetrics.py`** — the architecture signals: dependency
  cycles (`cycle_ratio`), coupling density, fan-in concentration, and Martin's
  A-I-D main-sequence distance.
- **`coherence_ratchet/signals.py`** — the signal *portfolio* in one place:
  `measure_all(root, repo=None)` returns duplication + architecture +
  connascence of meaning (significant literals shared across modules) + (with a
  git repo) hyperliminal coupling and contagion from the change history.
- **`coherence_ratchet/ratchet.py`** — the budget that can only hold or tighten.
  No single metric is enough (a fragmenting change can slip past any one of
  them), so the ratchet watches a **portfolio**: duplication, dependency cycles,
  and connascence. Coupling, fan-in, hyperliminal pairs, and contagion are
  reported as diagnostics beside it, never ratcheted. Also here: the append-only
  coherence-debt ledger.
- **`coherence_ratchet/cli.py`** — `measure`, `init`, `check`. `check` exits
  non-zero when a watched signal worsened past budget (the CI contract); `check
  --accept --owner NAME --trigger TEXT` turns a trip into an owned, dated ledger
  entry instead of a failure.
- **`playground/billing_states.py`** — the decay, commit by commit.
- **`demo.py`** — replays it and prints the curve and the ratchet decisions.

See `docs/worked-example.md` for the full portfolio run across the staged states
and a public repo (Flask), with every number reproduced.

## The derived self-model

The ratchet stops decay getting worse. The self-model is the other half: the shape a change should
move *toward*, derived from the code so it never goes stale.

```sh
coherence-ratchet selfmodel derive playground/_states/03-loyalty/billing --model coherence/selfmodel.json
coherence-ratchet selfmodel query "which sites compute retry?"           --model coherence/selfmodel.json
coherence-ratchet selfmodel query "does a helper for retry exist?"       --model coherence/selfmodel.json
coherence-ratchet selfmodel query "what is the canonical order shape?"   --model coherence/selfmodel.json
coherence-ratchet selfmodel query "what layer and deps does money have?" --model coherence/selfmodel.json
```

`derive` reads the tree (`coherence_ratchet/selfmodel.py`) and writes a JSON model: the module
dependency graph, a function index, entity shapes (dataclasses/TypedDict and implicit dict shapes with
their canonical keys and divergent sites), the conventions (shared literals), and the reuse helpers.
`query` (`coherence_ratchet/query.py`) answers over it deterministically. The key property is that it is
**derived**: add a new retry site, re-run `derive`, and the model shows it with no hand-editing — the
answer to "hand-maintained maps rot". An optional `--llm` flag (env-gated on `ANTHROPIC_API_KEY`) adds a
semantic matcher constrained to the derived candidates; the core runs offline with no key.

`selfmodel context <path>` renders the model as an **agent-grounding pack** — the canonical helpers to
reuse, the entity shapes to match, the conventions and the module layers — to feed an agent *before* it
writes a change. The full-context experiment (`experiments/fullcontext-fragmentation.md`) showed that
surfacing the canonical shape drove reuse from 0/3 to 3/3, so this is what turns "reuses if it happens to
see it" into "reliably sees it" — the mechanism that lets a team safely raise agent autonomy.

## The leading-indicator report

The method promises measurable leading indicators, not an ROI claim. `report` reads the coherence-debt
ledger (and optionally a git repo) and prints what a team can stand behind:

```sh
coherence-ratchet report --ledger coherence/coherence-ledger.jsonl [--repo .]
```

Ledger coverage (share of accepted debt that is owned **and** dated), open items by region, overdue
items (a repayment trigger whose date has passed), and how long the ratchet has held (days, or commits
with `--repo`). These are process indicators — the discipline working — not savings.

## The optional semantic gate (the second layer)

The deterministic ratchet is the floor — necessary but not sufficient. It flags duplicate clusters but
cannot tell *sanctioned* symmetry (blessed duplication) from *uncatalogued* fragmentation, and it cannot
see semantic layering violations. The `gate` command adds the LLM layer the experiments validated
(`experiments/semantic-detector.md`, `architecture-gate.md`, `gate-generalisation.md`):

```sh
coherence-ratchet gate playground/_states/03-loyalty/billing \
    --catalogue coherence/catalogue.example.json \
    --layering  coherence/layering.example.json
```

For each duplicate cluster the deterministic floor found, the gate asks an LLM to *match a specific
pattern in the ratified catalogue, or return NONE* — multi-trial (default 5), with a **conservative
quorum (default 4-of-5) to CLEAR**; anything short surfaces to the steward. It clears only what the
steward has blessed and never silently passes uncatalogued divergence, reproducing the experiments'
zero-dangerous-false-clears property. With a declared layering spec it also flags layer violations
(a free deterministic up-dependency check, plus an LLM misplaced-responsibility check when
`responsibilities` are declared).

It is **optional and env-gated on `ANTHROPIC_API_KEY`**, exactly like the self-model's `--llm` matcher:
with no key it prints a clean "skipped" (the deterministic layering check still runs), and the `check`
CI gate is untouched. With **no catalogue** it surfaces all duplication — the safe default. The gate's
quality is bounded by the catalogue the steward ratifies; it surfaces to a human and never auto-acts.

## The behaviour-complete proof (the third layer)

The gate says *whether* to consolidate; the proof says *whether the consolidation you made changed
behaviour*. The experiments showed characterisation suites are porous — a naive merge passed every test
while silently flipping `price_to_cents` rounding and a retry try-count. `prove` is the brake that
catches exactly that, by differential testing the original against the canonical replacement:

```sh
# does the canonical helper behave identically to the original it replaces?
coherence-ratchet prove "old/::billing.to_cents_legacy" "new/::billing.to_cents"
coherence-ratchet prove "src/::billing.retry_orig" "src/::billing.retry" --strategy retry_strategy.py
```

Each implementation is run over the same inputs — an **adversarial seed library aimed at the change
points** (half-boundary floats catch rounding flips; small integers catch off-by-one counts; the
exception set catches selectivity) plus type-driven generation — and their observed behaviour (return
value **and** raised-exception type) is compared. Verdict: **REFUTED** with a counterexample, or
**PROVED** up to the tested space. It exits non-zero on REFUTED, so it works as the consolidation gate
in CI, and `--out PROOF.md` writes the proof packet.

Honest framing: this is property-based differential testing — decisive at refutation, and "PROVED"
means no counterexample was found, not a formal equivalence proof. Side effects, I/O, time and
randomness are out of the deterministic core; the steward reviews those in the diff (`proof.py`). A
signature auto-generation can't build (a higher-order function like `retry(op)`) needs a `--strategy`
module supplying the inputs; scalar signatures like `to_cents(amount)` need no setup. This is the
engine/brake split: the integrator or agent consolidates, `prove` refuses to let a behaviour change
through silently.

## Run it

```sh
git clone https://github.com/RomanLobus/coherence-ratchet
cd coherence-ratchet
pip install -e .                             # installs the `coherence-ratchet` command
python3 demo.py                              # the curve + ratchet decisions

coherence-ratchet measure playground/_states/03-loyalty/billing
coherence-ratchet init    playground/_states/00-baseline/billing --budgets /tmp/b.json
coherence-ratchet check   playground/_states/03-loyalty/billing  --budgets /tmp/b.json   # exits 1
coherence-ratchet check   playground/_states/03-loyalty/billing  --budgets /tmp/b.json \
    --accept --owner billing-team --trigger "next settlement refactor"                    # exits 0, writes ledger

python3 -m pytest -q                         # or: python3 tests/run.py if pytest is absent
```

(Without installing, prefix any command with `python3 -m coherence_ratchet …`.)

## What it deliberately leaves out — and why

The deep-research pass on the method was blunt about where the risk lives, and
the MVP is scoped to match.

- **The LLM layers are optional and off by default.** The controlled experiments
  found an LLM confidently wrong as an autonomous judge of what should
  consolidate; the only framing that survived is objective matching against a
  human-ratified catalogue, surfacing to a steward. So `gate` and the
  self-model's `--llm` matcher are env-gated on `ANTHROPIC_API_KEY`, never
  auto-act, and everything else runs offline. The deterministic floor is the
  part a team can trust without trusting anything it cannot reproduce.
- **No consolidation engine.** The tool refuses a bad merge (`prove`); it does
  not perform the merge. Free-form LLM refactoring is unsafe roughly 7% of the
  time and characterisation tests alone miss most of those regressions, so
  performing the consolidation stays with the team or its agent, behind the
  proof.
- **Coupling is reported, not ratcheted.** Raw coupling is not lower-is-better:
  consolidation raises healthy coupling to the shared helper. Ratcheting *bad*
  coupling needs an allowed-dependency spec — a next step.
- **The similarity threshold is calibrated against this fixture** (in-family
  pairs score 0.43–1.0, unrelated functions below 0.20). A real codebase needs
  its own calibration.
- **O(n²) pairwise comparison.** Fine for a playground; a real tool needs LSH
  or MinHash bucketing.

## How it maps to the book

This is the *coherence ratchet* in the smallest honest form: the redundancy
metric is the **coherence budget** made concrete, the budget file is the
**ratchet**, and the JSONL record is the **coherence debt ledger**. Everything
the MVP omits is named in the book as the layer that needs care, evidence, or a
human in the loop — not hand-waved as done.

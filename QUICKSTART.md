# Quickstart: the first week, reproduced

This is the runnable mirror of the book's "Getting started" chapter. Every command below runs against
the staged billing subsystem in `playground/_states/`, and every number matches the chapter exactly.
Where the chapter says "a billing slice in the same shape as the checkout-pricing subsystem the book has followed", this is it.

Run from `ratchet-mvp/`. Nothing here needs a network or an API key.

## 0. Install the floor

```sh
pip install -e .
coherence-ratchet --help        # measure | init | check | selfmodel
```

The staged subsystem is one billing slice captured in five states: a clean baseline, three rounds of
AI-assisted change that each copy-and-diverge an existing behaviour, and a consolidated end state. The
"drifted" subsystem the chapter works on is `03-loyalty` — the loyalty feature nobody finished.

```sh
STATE=playground/_states/03-loyalty/billing
```

## 1. See the shape (self-model)

```sh
coherence-ratchet selfmodel derive $STATE --model coherence/selfmodel.json
coherence-ratchet selfmodel query "which sites compute retry?" --model coherence/selfmodel.json
```

Expected:

```
[concept]  subject: retry   matcher: deterministic
  exports.export_with_retry  (score 1)
  orders.submit_with_retry  (score 1)
  refunds.issue_refund  (score 1)
  retry.retry  (score 1)
  reuse: a 'retry' helper already exists -> retry.retry (duplicated in exports.export_with_retry, loyalty.award_points_retrying, orders.submit_with_retry)
```

Retry is implemented four times; `retry.retry` is the helper the other three drifted from. Other
questions the same model answers:

```sh
coherence-ratchet selfmodel query "does a helper for retry exist?"        --model coherence/selfmodel.json
coherence-ratchet selfmodel query "what layer and deps does money have?"  --model coherence/selfmodel.json
```

The model is **derived**. Add a fifth retry site to the tree, re-run `derive` with no hand-editing, and
the query shows it. That is the freshness property (the tool never asks anyone to refresh a map by hand).

Feed it to an agent before it writes a change — the grounding pack that makes reuse reliable:

```sh
coherence-ratchet selfmodel context $STATE > coherence/grounding.md
```

## 2. See the drift (portfolio)

```sh
coherence-ratchet measure $STATE
```

Duplication ratio 0.75, two redundant clusters, one shared literal. Note the diagnostic: as this
subsystem decayed from the baseline, coupling density *fell* (0.40 → 0.25), because each diverged copy
is a loosely connected new module. A coupling-only gate would have called the decay an improvement.
That is why the ratchet watches a portfolio and treats coupling as a diagnostic, never a target.

To see the whole progression:

```sh
for s in 00-baseline 01-orders 02-exports 03-loyalty 04-consolidated; do
  echo "== $s =="; coherence-ratchet measure playground/_states/$s/billing --json
done
```

| state           | duplication | clusters | connascence | coupling |
|-----------------|------------:|---------:|------------:|---------:|
| 00-baseline     | 0.00        | 0        | 0           | 0.40     |
| 03-loyalty      | 0.75        | 2        | 1           | 0.25     |
| 04-consolidated | 0.00        | 0        | 1           | 0.75     |

Consolidation drops duplication to zero and *raises* coupling to 0.75 (the shared helper). Healthy
coupling; exactly the fix the ratchet must reward and therefore must not ratchet.

## 3. Open the ledger

```sh
coherence-ratchet init  playground/_states/00-baseline/billing --budgets coherence/budgets.json
coherence-ratchet check $STATE --budgets coherence/budgets.json      # exits 1 — tripped
```

```
RATCHET TRIPPED — coherence worsened past budget:
  ✗ connascence_shared: 1 > ceiling 0 (+1)
  ✗ duplication_ratio: 0.75 > ceiling 0.0 (+0.75)
  ✗ redundant_clusters: 2 > ceiling 0 (+2)
  ✗ redundant_functions: 6 > ceiling 0 (+6)
```

Two honest branches: fold a copy back into `retry.retry`, or record the debt with an owner and a date.

```sh
coherence-ratchet check $STATE --budgets coherence/budgets.json \
  --accept --owner "billing-team" \
  --trigger "next reconciliation refactor / 2026-Q4" \
  --region "billing.loyalty" \
  --ledger coherence/coherence-ledger.jsonl        # exits 0 — writes a ledger line
```

```json
{"when": "...", "region": "billing.loyalty", "owner": "billing-team",
 "repayment_trigger": "next reconciliation refactor / 2026-Q4",
 "breaches": [{"metric": "duplication_ratio", "ceiling": 0.0, "observed": 0.75}, ...]}
```

Then read the ledger as leading indicators — coverage, overdue items, how long the ratchet has held:

```sh
coherence-ratchet report --ledger coherence/coherence-ledger.jsonl
```

These are process metrics (the discipline working), not an ROI claim.

## 4. Consolidate, and watch the portfolio find the next debt

```sh
coherence-ratchet check playground/_states/04-consolidated/billing --budgets coherence/budgets.json
```

Duplication is back to zero: the copies were folded into `retry.retry`. Coupling rose to 0.75, and the
ratchet does not care, because coupling is a diagnostic. But the check still trips, on one signal:

```
  ✗ connascence_shared: 1 > ceiling 0 (+1)
```

This is the portfolio doing exactly what a single duplication metric could not. The consolidation
repaid the obvious debt and left a subtler one: the retry count `3` is now hard-coded in two places,
`retry.retry(attempts=3)` and `loyalty.award_points_retrying(limit=3)`, agreeing by coincidence rather
than by a shared constant. The self-model names it:

```sh
coherence-ratchet selfmodel query "what conventions are there?" --model coherence/selfmodel.json
#   3  in loyalty, retry
```

That is the next week-two decision, surfaced automatically: either let `retry` own the default and have
loyalty call `retry(action)`, or accept the shared constant in the ledger with an owner and a date. A
duplication-only gate would have gone green here and hidden it. This is why the ratchet watches a
portfolio.

## 5. Wire it into CI

Add the check as a pipeline step against the real subsystem, with the budget file committed to the repo:

```sh
coherence-ratchet check billing/ --budgets coherence/budgets.json
```

Non-zero exit fails the build, the same contract as a coverage ratchet. A pull request that copies retry
a fifth time now stops and asks: reuse the helper, or open a ledger entry.

## 6. Optional: the semantic gate (the second layer)

The deterministic floor surfaced two duplicate clusters. The `gate` command adds the LLM layer that
decides which are *sanctioned* symmetry (clear) and which are *uncatalogued* fragmentation (surface):

```sh
export ANTHROPIC_API_KEY=sk-...        # optional; without it the gate skips cleanly
coherence-ratchet gate $STATE \
    --catalogue coherence/catalogue.example.json \
    --layering  coherence/layering.example.json
```

Each cluster is matched against the ratified catalogue over 5 trials; a cluster clears only on a 4-of-5
quorum to a specific pattern, otherwise it surfaces to the steward. With no key:

```
  semantic gate skipped — set ANTHROPIC_API_KEY (deterministic layering ran)
  (deterministic floor already flagged 2 duplicate clusters)
```

With no `--catalogue`, every cluster surfaces (the zero-false-clear default). The gate surfaces to a
human and never auto-acts; the deterministic `check` above stays the hard CI gate.

## 7. Optional: prove a consolidation preserved behaviour (the third layer)

When the team actually consolidates a cluster (folds the copies into the canonical helper), `prove`
differentially tests the canonical against each original before it is committed. The shipped fixtures
reproduce the silent changes the experiments found:

```sh
F=_fixtures/consolidation
# the integrator's silent rounding flip — REFUTED at the half-cent (auto-generated float seeds)
coherence-ratchet prove "$F::variants.to_cents_half_up" "$F::variants.to_cents_half_even"
# two retry divergences at once (try-count + exception selectivity) — REFUTED
coherence-ratchet prove "$F::variants.retry_orig" "$F::variants.retry_canon" --strategy $F/retry_strategy.py
# a genuinely faithful consolidation — PROVED
coherence-ratchet prove "$F::variants.retry_orig" "$F::variants.retry_faithful" --strategy $F/retry_strategy.py
```

The first two exit non-zero with a counterexample (`original returns 1 ≠ canonical returns 0` at
`0.005`); the third exits 0. That is the brake the experiments proved non-negotiable: a porous test
suite waves these through, `prove` does not.

## What this reproduces, and what it does not

Steps 0–5 are deterministic and offline — the floor a team can trust without trusting anything it cannot
reproduce. Step 6 adds the semantic layer (the LLM matcher), optional and env-gated, surfacing to a
steward rather than deciding. Step 7 adds the behaviour-complete proof — deterministic and offline
again — the brake that refuses a behaviour-changing consolidation. All three layers of the method now
run: `check` (floor) → `gate` (semantic) → `prove` (behaviour). What remains outside the tool is
*performing* the consolidation for you and comparing side effects / non-determinism; the steward owns
those. See `docs/worked-example.md` for a public-repo run (Flask) of the architecture signals.

# Quickstart: one honest pass through the method

Run this from the companion-repository root, the directory the clone leaves you in:

```sh
python3 -m pip install ./ratchet-mvp
python3 ratchet-mvp/tests/run.py
P=ratchet-mvp/playground/_states/06-checkout-cycle/checkout_pricing
mkdir -p coherence
```

`P` must point at the package directory itself. Pointed one level up, at the state directory, the tool refuses and names the package it can see, because a reading taken there finds no dependency edges and would otherwise look like a clean result.

This is the same fixture and the same working directory as the getting-started week in the book. If a command here cannot run from a clean installation, the book is not ready to ask a reader to trust it.

## 1. Observe and set the baseline

```sh
coherence-ratchet measure "$P"
coherence-ratchet init "$P" --budgets coherence/budgets.json \
  --by 'pricing region owner' --reason 'first baseline for the checkout-pricing region'
coherence-ratchet check "$P" --budgets coherence/budgets.json
```

The final command must pass unchanged. The baseline is not an ideal architecture; it is the line this region has agreed not to cross silently. `init` refuses without `--by`, and refuses to overwrite an existing budgets file without `--force`.

## 2. Derive the observed model

```sh
coherence-ratchet selfmodel derive "$P" --model coherence/selfmodel.json
coherence-ratchet selfmodel query 'order total' \
  --model coherence/selfmodel.json --intent coherence/intent.json
```

The model contains observations and candidates. A commonly used helper or entity-key intersection remains a candidate, not a policy. Inspect candidate IDs, then ratify one only after reviewing its evidence:

```sh
coherence-ratchet selfmodel ratify '<candidate-id>' \
  --model coherence/selfmodel.json --intent coherence/intent.json \
  --by 'pricing architecture owner' \
  --rationale 'one minor-unit conversion at the checkout seam' \
  --scope 'checkout-pricing seam'
```

## 3. Ground the agents in what was ratified

```sh
coherence-ratchet ground "$P" \
  --model coherence/selfmodel.json --intent coherence/intent.json
```

Writes a managed block into `AGENTS.md` and leaves every byte outside its markers alone. Statements carry `[OBSERVED]`, `[CANDIDATE]`, or `[RATIFIED]`, and the block says in its own words that only the ratified lines are instructions. The opening marker carries the model and tree hashes, which is what makes the next command possible:

```sh
coherence-ratchet ground "$P" --check \
  --model coherence/selfmodel.json --intent coherence/intent.json
```

Exits 0 while the block still describes the tree, and exits 2 with both hashes named once the source moves. Change the source after deriving and `derive`-dependent commands reject the stale model; change the model without re-ratifying and they reject the intent/model hash mismatch.

## 4. Measure a change against what was ratified

```sh
git add -A
coherence-ratchet advise "$P" --staged \
  --model coherence/selfmodel.json --intent coherence/intent.json
```

A ratified conflict names the canonical site, its approver and the date, and is the only class that may fail a build. A collision with something nobody ratified is surfaced and says so. `--fail-on ratified` is the default and `--fail-on none` is the only alternative; no value of the flag fails on a candidate. `--fail-on any` did, which is why it was removed.

Ratification records who decided and cannot verify it. `--by` takes a string, and a string looks the same whoever types it, so an agent with shell access can run this command. The MCP server refuses ratification and says why, which covers the interface and not the filesystem. Where the human-only property has to hold mechanically, put a `ratification-policy.json` beside the intent file:

```json
{
  "approvers": ["ada@example.com", "grace@example.com"],
  "require_signed_commit": true
}
```

`approvers` is checked against `--by` when you ratify; `require_signed_commit` is checked by `coherence-ratchet selfmodel verify-intent <intent>` in CI, against the commit that last changed the intent file. The file is absent by default and the check is silent when absent, so nothing changes until a team writes one. It buys attribution rather than authorship.

## 5. Sample history without checking out old commits

```sh
coherence-ratchet history "$P" --repo . --samples 24 \
  --json coherence/history.json
```

The sampler reads committed snapshots through `git archive`; it leaves HEAD and the working tree alone.

## 6. Accept exposure only with evidence

When `check` finds deterioration, CI fails. If the owner deliberately accepts it, record the decision rather than weakening the baseline anonymously:

```sh
coherence-ratchet check "$P" --budgets coherence/budgets.json \
  --accept --owner 'pricing team' \
  --trigger 'before contract v2 becomes the default' \
  --region 'checkout-pricing seam' \
  --volatility medium --coordination-span high \
  --criticality high --discoverability medium --blast-radius high \
  --evidence 'three independently deployed consumers' \
  --confidence high --review-date 2026-10-01 \
  --repayment-feasibility medium
```

This example resolves to `HIGH` exposure. If any required dimension lacks evidence, the only honest status is `NEEDS_ASSESSMENT`, written with `--needs-assessment`; a partial assessment offered without that flag is refused.

```sh
coherence-ratchet report --ledger coherence/coherence-ledger.jsonl
```

## 7. Compare a proposed consolidation

```sh
F=ratchet-mvp/_fixtures/consolidation
coherence-ratchet compare \
  "$F::variants.to_cents_half_up" \
  "$F::variants.to_cents_half_even"

coherence-ratchet compare \
  "$F::variants.retry_orig" \
  "$F::variants.retry_faithful" \
  --strategy "$F/retry_strategy.py"
```

The rounding mutation returns `REFUTED` with a counterexample. A faithful finite comparison returns `NO_DIVERGENCE_FOUND`, not equivalence. Unsupported signatures or inconclusive runs return `UNPROVEN`. Follow with `apidiff`, contract evidence where relevant, and human review.

## 8. Read the result correctly

The tool can show what exists, surface possible patterns, bind a human decision to evidence, put the ratified decisions where agents read them, stop unacknowledged worsening, and search a finite space for behavioural divergence. It cannot decide the organisation's architecture, forecast delivery cost, or establish arbitrary program equivalence.

Exit codes are uniform across every subcommand: 0 held, 1 the line was crossed, 2 the tool refused to measure or was misused, 3 advisory findings present, 4 could not measure.

The enterprise seam and formal-method examples live outside this CLI, and both need a toolchain the Python install does not carry:

```sh
enterprise-seam-lab/verify.sh
formal/verify.sh
```

## Edit notes

- Moved to the checkout-pricing fixture and the clone root, so this transcript and the book's getting-started week run the same commands in the same place. They previously used different fixtures from different working directories while the week called this file its tested transcript.
- Added the grounding, freshness-check and advise steps, and the exit-code contract.
- Kept the ratification, mismatch rejection, exposure evidence, history and comparison sections; removed catalogue-authority, monetary debt, and general proof language in an earlier pass.

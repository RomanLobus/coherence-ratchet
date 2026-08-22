# Coherence Ratchet reference implementation

This is the deliberately small, Python-focused companion for *Stewardship*. It demonstrates a maintenance practice; it does not automate architectural judgement.

The durable sequence is:

> observe → ratify → assess exposure → decide → ratchet → verify

The extractor is Python-specific. The judgement model is language-neutral, and the sibling `enterprise-seam-lab/` demonstrates a Python–TypeScript contract boundary.

## Install for local development

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
```

The command surface is `measure`, `init`, `check`, `selfmodel`, `gate`, `compare`, `report`, `history`, and `apidiff`.

## Four kinds of truth

`selfmodel derive` writes schema-v2 `coherence/selfmodel.json`. It records source revision and tree hash, extractor identity and ruleset hash, mechanically observed structure, and heuristic candidates. Frequency does not confer authority.

Human-owned `coherence/intent.json` records ratified contracts and conventions, including approver, date, rationale, scope, exceptions, and source-model hash. `selfmodel ratify` is the only path from candidate to ratified intent.

Queries and grounding packs label statements `[OBSERVED]`, `[CANDIDATE]`, or `[RATIFIED]`. Only the last class can issue an imperative instruction. `context` re-derives the source and refuses to render when the saved model is stale or the intent hash does not match.

## Exposure, not price

Accepted ledger entries assess five dimensions as `low`, `medium`, or `high`: volatility, coordination span, criticality, discoverability, and blast radius. Missing evidence yields `NEEDS_ASSESSMENT`; complete records resolve to `LOW`, `MODERATE`, or `HIGH`. Repayment feasibility is recorded separately. There is no currency estimate and no summed score.

## Verification vocabulary

`compare` performs bounded differential testing. Its terminal statuses are:

- `REFUTED`: a counterexample was found.
- `NO_DIVERGENCE_FOUND`: no difference appeared in the stated tested space.
- `UNPROVEN`: the case was unsupported or inconclusive.

API and schema compatibility checks are separate evidence. Human review remains responsible for side effects, nondeterminism, environmental assumptions, and whether the intended semantics are correct. `FORMALLY_VERIFIED_IMPLEMENTATION` and `MODEL_CHECKED` are reserved for the bounded examples in `../formal/`; neither label transfers to unrelated Python.

## Ratchet semantics

`init` captures the current baseline. An unchanged `check` passes. A check trips only when a watched measure worsens beyond its ceiling. Improvement can lower the ceiling with `--tighten`; accepted deterioration requires an owner, trigger, review date, evidence, confidence, all five exposure dimensions, and repayment feasibility.

`history` samples committed revisions through `git archive`; it does not change the working tree or repository HEAD.

## Evidence boundary

The fixtures are `REPRODUCIBLE_FIXTURE` evidence. Results obtained from public repositories are bounded observations, not forecasts of later cost. The optional LLM gate surfaces semantic residue to a steward; it does not ratify intent. See `../BOOK-CONTRACT.md`, `../formal/README.md`, and `../enterprise-seam-lab/README.md` for the complete claim boundary.

## Edit notes

- Replaced the v0.1 catalogue-and-proof description with the v0.2 truth, exposure, ratchet, and comparison contracts.
- Made the Python extractor boundary and human decision boundary explicit.
- Removed publication claims pending repository security and release gates.

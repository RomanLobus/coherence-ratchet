# Experiment index: how far each write-up can be checked

Every write-up in this directory is classed by how far a reader can check it. Class A write-ups are deterministic: a script or committed fixture in this repository reproduces the numbers with no language-model call. Class B write-ups are language-model probes that re-run against an API key, from a committed harness and fixture. Class C write-ups are recorded runs: documented in full (design, counts, caveats) but not mechanically re-runnable, usually because the trial fixtures lived in a session scratchpad rather than the repository, or because the judging prompts and catalogues were never committed. Where a write-up sat between B and C, it is classed C and the notes column says why.

## Open: the longitudinal dumps do not fully re-verify (12 August 2026)

`longitudinal_arch.py --verify` against the pinned SHAs fails on flask and requests, on two
independent clones. Every figure the manuscript quotes reproduces exactly; the drift is in
early-history edge counts and the values derived from them (coupling, instability, D, dmods, pain),
and in two early cycle-ratio points. The one claim affected is that flask read essentially zero from
2010 to 2012.

This was found by adding the cycle numerator to the dumps (N4) and checking that no prior number
moved. The numerator work is on hold behind it: re-emitting the dumps now would bake in numbers that
contradict the printed prose, and the honest order is to find why the analyser and the dumps
disagree first. `tools/evidence-check.sh` is the guard for exactly this and had never run against a
clean clone.


## Promoting a class C write-up

`experiments/harness/` is the dispatcher these records were missing. Several probes already exposed
the right interface — a `build_prompt(condition)` that embeds a committed fixture, and a
deterministic `score_code(...)` with no model in the loop — and what was absent was the middle:
dispatch N trials to a pinned model, persist the raw responses, and stamp what produced them.

    python3 experiments/harness/dispatch.py --probe probe_fullcontext_fragmentation.py \
        --trials 10 --model claude-haiku-4-5-20251001 \
        --out experiments/data/runs/fullcontext/2026-08-12-haiku-4-5
    python3 experiments/harness/dispatch.py --probe … --rescore <run-dir>   # no model call
    python3 experiments/harness/dispatch.py --probe … --verify  <run-dir>   # prompt drift since the run

A promotion needs four things committed together: the fixture tree, the prompt builder, a
deterministic scorer with no model in the loop, and the run manifest. The dispatcher refuses an
undated model alias, records a failed trial rather than dropping it, and keeps the raw response so a
reader without an API key can still dispute the scoring — and so a retired model snapshot does not
take the evidence with it.

A promoted entry is **not** class A. A sampled model is not a deterministic fixture, so the honest
wording is *reproducible-as-recorded against a pinned snapshot*, never *reproducible*, and the
corresponding row in `EXPERIMENT-INDEX.md` carries `RECORDED_RUN` until its four artefacts are in
the tree.

Honestly counted, the dispatcher alone reaches about twelve of the class C write-ups — the ones whose
scorer already exists or is a few dozen lines away. Roughly five more need a scorer written first
(schema-overlap and layout-identity). The gate experiments need committed catalogues rather than a
dispatcher. And `advice-process.md` and `human-review-burden.md` should not be promoted at all: they
use a model as a stand-in for a person, and re-running them at a larger n makes a masking artefact
more precise without answering the question.

Two boundary notes. The class A corpus probes (`probe_*.py`, `longitudinal.py`, `longitudinal_arch.py`) analyse public libraries (requests, flask, httpie, boltons, sqlalchemy); re-running them needs local clones and an edit to each script's hard-coded repository path. And where a class C write-up has a deterministic portion the shipped tool does reproduce (the triage funnel's top half, the flask ratchet trajectory), that is recorded in the notes. Paths in the re-run column are relative to `ratchet-mvp/`.

| write-up | class | headline result | where to re-run | notes |
|---|---|---|---|---|
| `advice-process.md` | C | lone steward 3/3 LEAVE vs advice process 3/3 CONDITIONAL; neither made the naive merge | recorded | LLM proxy masks the human value of the advice process |
| `advise-detector-boundary.md` | A | the shipped structural detector named a collision in 0 of 10 real blind reinventions; it names them on copy-and-diverge | stage each committed `task_only` response into the fixture and run `coherence-ratchet advise --staged` | deterministic, no API key; bounds which loop the deterministic command can close |
| `api-contract-check.md` | A | breaking consolidation caught, compatible merge cleared; the shipped playground consolidation flagged BREAKING | `probe_api_contract.py` + `_fixtures/apidiff/` + `playground/_states/` | |
| `architect-agent.md` | C | free-form 5/5 distinct Order schemas; architect-first 4/5 identical to the canonical | recorded | |
| `architecture-decay.md` | A | flask cycle_ratio 0.00 → 0.83, coupling 1.0 → 4.2; requests coupling 0.97 → 4.21; httpie 0.33 → 0.05 → 0.15; boltons 0.00 | `longitudinal_arch.py` (last run committed as `longitudinal_arch_out.json`) | needs local clones of the four libraries |
| `architecture-gate.md` | C | 6/6 recall on three injected smells; catalogue constraint cut extra findings 0.8 → 0.2 per trial | recorded | |
| `architecture-model-conformance.md` | C | eight agents: 4 distinct free-form module layouts → 1 identical layout under the declared model | recorded | |
| `architecture-ratchet.md` | A | a hold-or-lower cycle_ratio ratchet would have flagged 7/13 (flask), 8/14 (requests), 5/15 (httpie) measurable intervals; gated 7, 5 and 4 | `scripts/ratchet_replay.py` → `data/ratchet_replay.json` | raw counts read from the committed dumps (no network); `--with-gate` needs local clones. The record's original 30/43, 48/49, 38/50 came from an uncommitted dense sweep and are superseded |
| `autonomous-consolidation.md` | C | scoped, proof-gated consolidation safe 20/20; the naive merge passes the characterisation suite | recorded | |
| `catalogue-pattern-consistency.md` | C | duplication proxy inverts (1.00 coherent vs 0.00 fragmented); catalogue-match gate scores 5/5 and 0/5 correctly | recorded | |
| `change-driver-cochange.md` | A | flask `_make_timedelta` co-change 0.94 (consolidate) vs deliberate API mirrors 0.09–0.12 (leave) | `probe_cochange.py` | needs local clones |
| `checkout-fixture.md` | A | cycle ratio 0.0 → 0.5 (the one breach); 5 redundant functions in 2 clusters; 1 hyperliminal pair, contagion 1.8 | `tests/test_checkout_fixture.py` + `playground/checkout_states.py` + `experiments/scripts/checkout_history_repo.py` | every number pinned in CI |
| `codemod.md` | C | merged both exact-duplicate pairs with byte-identical behaviour; left the divergent retry intact | recorded | deterministic AST demo, but the script was not committed |
| `combined-priority.md` | A | locality × degree × co-change ranks `_make_timedelta` first; connascence-alone inverts the ranking | `probe_priority.py` | needs local clones |
| `connascence-prevention.md` | C | non-default convention: control diverges 3/3, surfaced conforms 3/3; helper reuse 0/5 → 5/5 | recorded | |
| `connascence-signal.md` | A | `'utf-8'` in 6 requests modules (24 occurrences); 56 shared literals in requests, 70 in flask | `probe_connascence.py` | needs local clones |
| `consolidation-harder.md` | C | 20/20 safe on the trap fixture; the naive consolidation passes characterisation and fails the oracle on both traps | recorded | |
| `constrain-by-design.md` | C | pinned contract: 1 API shape, 1 key scheme, 12/12 identical happy-path output | recorded | |
| `cross-cutting-and-naming.md` | C | 5/5 same logging library, conventions fragment beneath it (2 levels, 3 formats, 5 error shapes, 4 entity names); detector 5/5 | recorded | |
| `cross-language-detector.md` | C | precision 1.000, recall 0.836 across Python/JavaScript/Go/Java (40 functions, consensus voting) | recorded | the 40-function set and prompts were not committed, so C rather than B |
| `crosshair-boundary.md` | A | CrossHair finds the rounding divergence and exhausts on the retry pair | `crosshair_probe.py` (crosshair-tool 0.0.109, run 1 Aug 2026) | |
| `decomposition-and-norms.md` | C | sliced 0.80 vs coherent 0.27 duplication; consolidate-first norm → 0.00 | recorded | |
| `dependency-sprawl.md` | A | single-use third-party imports 6/3/6 (flask/requests/httpie); requests churn 0 → 53 → 10 | `probe_dep_sprawl.py` | needs local clones |
| `design-memory-decay.md` | C | note-only reuse 2–3/11; importable-pointer reuse 10–11/11; unpruned note grew ~10× | recorded | |
| `design-memory.md` | C | no memory 0.62 duplication; with memory 0.00 (n=1 per arm) | recorded | |
| `entity-ensemble-distribution.md` | B | across 40 ensembles over two families, independent agents produced a mean 2.75 and 1.60 distinct order shapes per five; ratified grounding collapsed both to exactly one, 20/20 and 19/19 ensembles in full agreement | `experiments/harness/dispatch.py --probe probe_entity_ensemble.py`; responses in `experiments/data/runs/ensemble/` | measures the rate the n=1 record could not; five-from-five did not occur once, so the original headline is its tail |
| `entity-coherence.md` | C | five independent agents produced five incompatible Order schemas; detector flagged the fragmentation 5/5 | recorded | |
| `entity-trap-demeter.md` | C | 4/4 agents produced responsibility-separated layouts (entity-trap hypothesis not supported); consolidation moved coupling 0 → 6 edges | recorded | |
| `feedback-loop.md` | C | detector feedback flipped reinvention to reuse 0/10 → 10/10; detector caught the collision 10/10 | recorded | |
| `feedback-loop-harnessed.md` | B | 0/10 reuse before feedback, detector fired 10/10, 10/10 reuse after, on gpt-5.4 with every stage committed | `experiments/harness/dispatch.py --probe probe_feedback_loop.py` | the flagship loop made re-runnable; needs the semantic detector, and round two is a reconstructed prompt rather than a live session |
| `fitness-functions.md` | C | three fitness functions fire on the layering, cycle and entity-shape violations and pass the clean cases | recorded | a few lines of deterministic Python, not committed; reuses scratchpad fixtures |
| `fullcontext-fragmentation.md` | B | task-only 0/10 reuse; every in-context condition 10/10, including adversarially buried naming (replicated 12 Aug 2026, n=10, `claude-haiku-4-5-20251001`) | `experiments/harness/dispatch.py --probe probe_fullcontext_fragmentation.py`; raw responses in `experiments/data/runs/fullcontext/2026-08-12-haiku-4-5` | reproducible-as-recorded against a pinned snapshot, not deterministic. Ceiling effect at subsystem scale: cannot discriminate context from surfacing, so it carries the floor result only |
| `gate-generalisation.md` | C | 8/8, 6/6 and 7/7 correct dispositions on requests, boltons and flask; review lists 8 → 3, 6 → 4, 7 → 4; zero dangerous false-clears | recorded | clusters re-derivable with the shipped detector; catalogues and prompts not committed |
| `goodhart-redteam.md` | C | a fully fragmented variant passes the cycle-only gate at duplication 0.60 | recorded | |
| `human-review-burden.md` | C | LLM reviewer proxy 10/10 in all three visibility conditions, masking the human cost | recorded | |
| `integrator-agent.md` | C | duplication 0.80 → 0.00, but the merge silently changed a rounding mode | recorded | |
| `longitudinal-decay.md` | A | flask 0.43 → 0.264, requests ~0.19 → 0.164, boltons 0.31 → 0.255; the one AI-heavy repo ~0.25 at 79 functions | `longitudinal.py` | needs local clones; the treatment-arm GitHub search is not reproducible |
| `main-sequence-distance.md` | A | abstractness ≈ 0.0 across all four histories; D degenerates to 1 − instability; instrument dropped | `longitudinal_arch.py` + `longitudinal_arch_out.json` | needs local clones |
| `mmi-composite.md` | A | MMI ranks boltons 8.17 > httpie 5.90 > requests 3.37 > flask 3.22; flask trajectory 6.32 → 3.22 | `probe_mmi.py` | needs local clones |
| `per-commit-differential.md` | C | null and confounded; the AI-heavy repo consolidated in 76% of its divergence-moving commits | recorded | deterministic git analysis, but the script was not committed |
| `no-chokepoint.md` | B | with no chokepoint to route through, blind consistency is 0/30 and the derived self-model reaches both sites 30/30 | `experiments/harness/dispatch.py --probe probe_nochokepoint.py`; responses in `experiments/data/runs/nochokepoint/2026-08-12-haiku-4-5` | answers the caveat `reframe-A-self-model.md` raised against itself; execution oracle, not inspection; a harness extraction bug found and corrected during scoring |
| `portfolio-redteam.md` | C | 5/5 adversarial trials evaded all three deterministic gates; 4/5 carried a silent rounding-mode divergence | recorded | |
| `prevention-reuse-or-justify.md` | C | visible helper: 10/10 in both arms (lift 0.00); hidden helper: 0/10 → 10/10 when surfaced | recorded; superseded for the visible-helper arm by `exhortation-null-harnessed.md` | |
| `exhortation-null-harnessed.md` | B | visible helper, exhortation vs none: 20/20 in both arms on two families, lift +0.00 | committed fixture, prompt builder and deterministic scorer; raw responses committed | |
| `reframe-A-self-model.md` | C | cross-cutting consistency 1/8 blind → 8/8 with the derived self-model; re-derivation auto-absorbed a third site | recorded | the self-model deriver itself ships in `coherence_ratchet` |
| `reframe-B-emergent-canon.md` | C | the modal pattern passed the correctness oracle 10/10 on all four trap concepts | recorded | |
| `reframe-C-convergence.md` | C | schema overlap 0.68 → 0.92 after one round; 4 distinct schemas remain on cosmetic residue | recorded | |
| `reframe-D-coherence-price.md` | C | coherence-price nudge lifted true reuse 4/10 → 6/10 over surfacing; no force-fitting (backoff kept 10/10) | recorded | |
| `reframe-E-ai-maintainer-cost.md` | C | fragmented matched coherent 8/8 vs 8/8 on a fully visible cross-cutting change | recorded | |
| `reframe-Eb-beyond-context.md` | C | 7/8 with the divergent site hidden; agents escaped via a shared upstream chokepoint | recorded | |
| `reframe-F-cell-blast-radius.md` | C | synthesis: coherence at the contract, freedom within the cell | recorded | no run of its own; draws on the chain's probes |
| `res-contagion-and-criticality.md` | C | contagion scales with divergent sites (3–4× blast radius); criticality stop rule anchored on RES2 | recorded | the contagion numbers re-run via `probe_hyperliminal.py` |
| `res-derived-vs-mapped.md` | C | fresh derived spec survived 3/3 stressors; stale hand-map 1/3, both failures at the unmapped fourth site | recorded; regime-dependent, see `derived-vs-mapped-harnessed.md` | |
| `derived-vs-mapped-harnessed.md` | B | failed replication: 20/20 in all three visible arms, 0/20 in both hidden arms; naming a site an agent cannot read does not get it changed | committed fixture, prompt builder, deterministic scorer; 140 trials | |
| `res-hyperliminal.md` | A | hyperliminal pairs 0/4/8 (requests/flask/httpie), including `argparser` ↔ `definition` co-changed 21 times with no static edge; mean contagion 1.28/1.56/2.05 | `probe_hyperliminal.py` | needs local clones |
| `res-residual-index.md` | C | residual index +0.00 in both discoverable regimes (5/5 vs 5/5; 3/3 vs 3/3) | recorded | |
| `res-stress-response.md` | A | httpie's `rich_*` and `man_pages` family co-changes at Jaccard 0.6–0.75 with almost no import edges (7 combine candidates); 0 elsewhere | `probe_stress_response.py` | needs local clones |
| `retrieval-quality.md` | C | reuse 10/10 at 5 and 24 catalogue entries and across a vocabulary gap; ranker recall@3 10/10 | recorded | |
| `scale-visibility-threshold.md` | C | 9/9 reuse up to 122 modules when the helper is lexically findable; 6/6 reinvent under jargon naming at the same size | recorded | |
| `scale-visibility-toolless.md` | B | with 122 modules in context and no tools, gpt-5.4 reuses the helper 40/40 whatever it is named; haiku-4-5 shows a 25-point naming gap that does not clear the 30-point rule at n=20 | `experiments/harness/dispatch.py --probe probe_scale_visibility.py`; responses in `experiments/data/runs/scale/` | bounds the scale claim to its retrieval form; the discoverability wall does not appear for a toolless agent with the package in context |
| `semantic-detector.md` | C | AST detector caught 2/4 divergent retries and 0/2 paginators; LLM clustering recovered every group 5/5 trials, zero false merges | recorded | |
| `semantic-gate-on-requests.md` | C | intent judging failed twice (0.97 self-agreement, unanimously wrong on the hash helpers; the clearing framing auto-cleared all 8); catalogue-matching then disposed 8/8 correctly | recorded | clusters re-derivable with the shipped detector; catalogues and prompts not committed |
| `semantic-precision-at-scale.md` | C | precision 1.000 and recall 1.000 on 56 functions across 8 concepts under 3-of-5 consensus | recorded | |
| `sham-grounding.md` | B | a false grounding block naming non-existent helpers is ignored 0/10 with the source in context, and obeyed 10/10 without it, producing ten modules that fail at import | `experiments/harness/dispatch.py --probe probe_fullcontext_fragmentation.py --condition full_sham --condition task_sham`; responses in `experiments/data/runs/fullcontext/2026-08-12-sham` | the control the grounding results needed: kills the placebo explanation and bounds the danger to agents that cannot verify |
| `shared-kernel-seams.md` | A | shared-kernel seams 19/15/29 (requests/flask/httpie); pooled co-change AUC 0.565 | `probe_shared_kernel.py` | needs local clones |
| `spec-regeneration.md` | C | 12 regenerations from an intent spec: 10 API shapes, 4 return types, 6 response key schemes | recorded | |
| `stamp-coupling.md` | A | fixture: 2/2 stamp sites caught, control clean; naive mode 22/48 false positives on requests/flask → 0/0 in data-contract mode | `probe_stamp_coupling.py` + `_fixtures/stampy/` | corpus half needs local clones |
| `triage-funnel-at-scale.md` | C | 6,342 functions → 797 clusters in 47 s on SQLAlchemy; a four-entry catalogue cleared 6/12 of a sampled dozen | recorded | the top of the funnel re-runs deterministically with the shipped CLI on a SQLAlchemy checkout; the gate sample does not |
| `ul-boundary-violation.md` | A | clean null: 0 ubiquitous-language violations across requests, flask and httpie (every domain type has a single home) | `probe_ul_violation.py` | needs local clones |
| `volatility-gated-ratchet.md` | A | requests flags 9 → 4 (3 verified frozen-module suppressions + 2 denominator artefacts), httpie 5 → 4, flask unchanged; zero live-decay misses | `probe_volatility_ratchet.py` | needs local clones |

A: 19, B: 8, C: 43 of 70.

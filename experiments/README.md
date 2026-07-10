# Experiments — the first-party evidence, indexed

These are the lab notebooks behind the book's first-party claims: 58 write-ups, each recording
what was asked, what ran, the numbers that came out, and the limits. They ship as provenance —
negative results and dead ends included — because a method whose discards are shown is more
trustworthy than one that only presents its survivors.

## How to read this index

Every write-up is classed by how far a reader can check it:

- **A — deterministic (13).** A script in `scripts/` or a tool command reproduces the numbers
  with no LLM involved. Where a script needs the public-repo corpus, see the setup below.
- **B — re-runnable LLM probe (1).** The procedure, prompts, script, and fixture all ship;
  re-running needs an `ANTHROPIC_API_KEY` and will vary with the model behind it.
- **C — recorded run (44).** The write-up reports a run whose fixtures or transcripts are not
  shipped. The claim is documented, not mechanically re-runnable from this repository.

Two honest provenance gaps, stated rather than patched. First, the LLM-based write-ups record
the model family (Claude) but not exact model IDs or run dates; treat every class-B/C result as
a demonstration of a mechanism, not a field effect size — the book says the same. Second,
artefact paths of the form `scratchpad/...` refer to the author's local run archive, which does
not ship; what ships is the write-up, the scripts, and the fixtures under `_fixtures/` and
`playground/`. New write-ups pin model ID and run date, and ship their fixtures.

Notation kept for provenance: `→ book: Ch.X` lines route a result to the chapter of the
companion book that carries it; codenames such as `P1`–`P12`, `R1`–`R10`, `D5`/`D6`, `H1`–`H6`
and the `reframe-A`…`F` letters are internal experiment-series identifiers, left as written.

## Corpus setup for the class-A scripts

Several deterministic scripts measure public libraries. Clone them once and point `CR_CORPUS`
at the directory (default `/tmp/gh-test`):

```sh
mkdir -p /tmp/gh-test && cd /tmp/gh-test
git clone https://github.com/psf/requests
git clone https://github.com/pallets/flask
git clone https://github.com/httpie/cli httpie
git clone https://github.com/mahmoud/boltons
```

The longitudinal scripts walk each library's git history (roughly two dozen sampled commits per
repository), so clone with full history for those; the recorded output of the architecture run
ships as `data/longitudinal_arch_out.json`.

## Index

| file | headline result | how to reproduce | class | model/date pinned? |
|---|---|---|---|---|
| advice-process.md | Both arms avoided naive merge 3/3; lone steward LEAVE ×3, advice process CONDITIONAL ×3 — richer, actionable verdict | recorded run only | C | no |
| architect-agent.md | Free-form gave 5/5 distinct Order schemas; architect-first gave 4/5 identical to canonical — fragmentation prevented up front | recorded run only | C | no |
| architecture-decay.md | Architecture decays under human maintenance: flask cycle_ratio 0.0→0.83 over 16 years while function duplication fell | `scripts/longitudinal_arch.py` (+ `data/longitudinal_arch_out.json`) | A | n/a |
| architecture-gate.md | 6/6 recall on all three injected smells; catalogue constraint cut false findings 0.8→0.2 per trial | recorded run only | C | no |
| architecture-model-conformance.md | Declared model collapsed 4 distinct module layouts to 1 identical across 8 variants; zero cycles either way | recorded run only | C | no |
| architecture-ratchet.md | cycle_ratio ratchet would have flagged 30/43 flask intervals; decay was small un-arrested increases, 0.0→0.83 | recorded run only | C | n/a (no LLM) |
| autonomous-consolidation.md | Scoped proof-gated consolidation safe 20/20 vs ~7% free-form breakage; char suite porous, safety came from agent care | recorded run only | C | no |
| catalogue-pattern-consistency.md | Duplication proxy sign-inverts (coherent 1.00 "bad", fragmented 0.00 "clean"); catalogue-match gate correct, 3 unanimous trials | recorded run only | C | no |
| change-driver-cochange.md | Co-change discriminates: accidental copy 0.94 (consolidate) vs intentional API symmetry 0.09–0.12 (leave) | `scripts/probe_cochange.py` (corpus) | A | n/a |
| codemod.md | AST codemod merged both exact-duplicate pairs (5→3 defs), behaviour identical, correctly left divergent 4-try variant | recorded run only | C | n/a (no LLM) |
| combined-priority.md | locality × degree × co-change ranks genuine copy first (5.65), demotes deliberate mirrors (1.39); each signal alone fails | `scripts/probe_priority.py` (corpus) | A | n/a |
| connascence-prevention.md | Non-default convention: control diverged 3/3 to HALF_UP; surfacing gave 3/3 conform and 5/5 helper reuse | recorded run only | C | no |
| connascence-signal.md | Cross-module shared literals — 56 (requests), 70 (flask) — invisible to duplication detector; signal floods, needs ranking | `scripts/probe_connascence.py` (corpus) | A | n/a |
| consolidation-harder.md | 20/20 safe on harder traps (unrepresentable metric site, module flag), with and without comments; zero silent breakage | recorded run only | C | no |
| constrain-by-design.md | Pinned contract collapsed 10 distinct APIs and 6 key schemes to 1 each (n=12); unpinned edges still diverged | recorded run only | C | no |
| cross-cutting-and-naming.md | Error handling 5/5 distinct, 4 names for one actor; detector caught both facets 5/5 trials | recorded run only | C | no |
| cross-language-detector.md | Concept clustering across 4 languages: precision 1.000, recall 0.836; 85% cross-language pairs co-grouped, never grouped by language | recorded run only | C | no |
| decomposition-and-norms.md | Slicing work into 5 agents roughly tripled duplication (0.80 vs 0.27); consolidate-first norm cut residual to 0.00 | recorded run only | C | no |
| design-memory-decay.md | Note-only reuse 2–3/11; importable helpers 10–11/11; unpruned note accretes ~10×; size budget costs nothing | recorded run only | C | no |
| design-memory.md | Design memory cut duplication 0.62→0.00 (n=1 per condition); no-memory agents built three to_cents, two retry loops | recorded run only | C | no |
| entity-coherence.md | Five independent agents produced 5/5 mutually incompatible Order schemas; detector flagged the fragmentation 5/5 trials | recorded run only | C | no |
| entity-trap-demeter.md | 4/4 agents responsibility-separated, no entity god-module; consolidation traded dup 0.60→0.375 for coupling edges 0→6 | recorded run only | C | no |
| feedback-loop.md | Detector-driven feedback flipped reuse 0/10 → 10/10; detector flagged the duplication 10/10 | recorded run only | C | no |
| fitness-functions.md | Three deterministic fitness functions: layering FAIL, flask 1 cycle / 20 modules FAIL, 5-schema entity divergence FAIL | recorded run only | C | n/a (no LLM) |
| fullcontext-fragmentation.md | Task-only reinvented 3/3; full context reused 3/3 even with buried helpers; reinvention only when helper absent | `scripts/probe_fullcontext_fragmentation.py` + `_fixtures/fullcontext` | B | no |
| gate-generalisation.md | Catalogue gate replicated on requests/boltons/flask: 8/8, 6/6, 7/7 correct dispositions, zero dangerous false-clears | recorded run only | C | no |
| goodhart-redteam.md | Fully fragmented variant passed cycle-only gate at cycle_ratio 0.0 while dup_ratio hit 0.60 | recorded run only | C | no |
| human-review-burden.md | Inconclusive: LLM reviewer caught the missed site 10/10 in all conditions — proxy too capable to expose human cost | recorded run only | C | no |
| integrator-agent.md | Integrator cut duplication 0.80→0.00 keeping all capabilities, but silently switched price_to_cents to ROUND_HALF_EVEN | recorded run only | C | no |
| longitudinal-decay.md | Human baseline flat-to-declining over 12–15 years (flask 0.43→0.24); AI treatment arm unmeasurable, repos weeks old | `scripts/longitudinal.py` (corpus, full history) | A | n/a |
| main-sequence-distance.md | Negative: abstractness ≈0.0 across four libraries' whole histories; D degenerates to 1−I, moves opposite real decay | `scripts/longitudinal_arch.py` + `data/longitudinal_arch_out.json` | A | n/a |
| mmi-composite.md | MMI discriminates: boltons 8.17 > httpie 5.90 > requests 3.37 > flask 3.22, matching cycle_ratio; flask 6.32→3.22 | `scripts/probe_mmi.py` (corpus) | A | n/a |
| per-commit-differential.md | Null, confounded: AI-heavy repo consolidated in 76% of divergence-moving commits; human comparators barely moved | recorded run only | C | n/a (no LLM) |
| portfolio-redteam.md | 5/5 adversarial trials evaded all three deterministic gates; 4/5 carried silent rounding-mode divergence | recorded run only | C | no |
| prevention-reuse-or-justify.md | Helper visible: 10/10 reuse with or without instruction; not surfaced: 0/10; surfacing flipped to 10/10 (lift 1.00) | recorded run only | C | no |
| reframe-A-self-model.md | Derived self-model lifted cross-cutting consistency 1/8 → 8/8 and auto-detected a newly added third site | recorded run only (deriver ships: `coherence_ratchet/selfmodel.py`) | C | no |
| reframe-B-emergent-canon.md | Modal pattern sound 10/10 on all four trap concepts; entrenchment risk untriggered — ratify-with-veto adopted | recorded run only | C | no |
| reframe-C-convergence.md | One mutual-visibility round lifted field-overlap 0.68→0.92, but 4 of 6 schemas stayed distinct on cosmetic residue | recorded run only | C | no |
| reframe-D-coherence-price.md | Coherence price nudged true reuse 4/10→6/10 over surfacing; backoff retained 10/10, no force-fitting | recorded run only | C | no |
| reframe-E-ai-maintainer-cost.md | Incoherent codebase 8/8 full success vs coherent 8/8; incoherence cost relocates to contracts and beyond-context scale | recorded run only | C | no |
| reframe-Eb-beyond-context.md | With divergent site hidden: incoherent 7/8 vs coherent 8/8; only 1/8 divergence bug; agents routed via chokepoint | recorded run only | C | no |
| reframe-F-cell-blast-radius.md | Synthesis, no new run: pin contracts, disposable internals; assembles E (8/8=8/8), D5 (4 layouts to 1) | synthesis of prior probes | C | no |
| res-contagion-and-criticality.md | Contagion 3–4x blast in fragmented fixtures; httpie mean blast 2.05 (tail 22); coherent subsystem at criticality, Ri=0 | `scripts/probe_hyperliminal.py` (contagion part; criticality recorded) | C | no |
| res-derived-vs-mapped.md | Fresh derived spec survived 3/3 stressors; stale hand-map 1/3, failures at the unmapped 4th site | recorded run only | C | no |
| res-hyperliminal.md | Hyperliminal pairs: requests 0, flask 4, httpie 8; mean blast up to 2.05, max 22 | `scripts/probe_hyperliminal.py` (corpus, git history) | A | n/a |
| res-residual-index.md | Ri = +0.00 both variants: fragmented survived 5/5 and 3/3 stressors, equal to coherent | recorded run only | C | no |
| res-stress-response.md | httpie: 7 combine-candidates, 5 not import-linked; requests/flask/sqlalchemy: 0 at J>=0.5 | `scripts/probe_stress_response.py` (corpus) | A | n/a |
| retrieval-quality.md | Reuse 10/10 in flood-5, flood-24 and ranker conditions (both runs); control 0/10; recall@3 10/10 | recorded run only | C | no |
| scale-visibility-threshold.md | 9/9 reuse at 4–122 modules when helper lexically findable; 6/6 reinvent when jargon-named | recorded run only | C | no |
| semantic-detector.md | LLM clustering 5/5 trials grouped all divergent functions, 0 false merges; AST detector caught 2/4, 0/2 | recorded run only | C | no |
| semantic-gate-on-requests.md | Subjective framings failed (2/2 dangerous clears); catalogue-matching worked: 0/2 dangerous, 8/8 correct; boltons 6/6 | recorded run only | C | no |
| semantic-precision-at-scale.md | 56 functions, 3/5 consensus: precision 1.000, recall 1.000, F1 1.000, zero false merges | recorded run only | C | no |
| shared-kernel-seams.md | Seams detected: requests 19, flask 15, httpie 29; co-change risk weak, pooled AUC 0.565 | `scripts/probe_shared_kernel.py` (corpus) | A | n/a |
| spec-regeneration.md | Formula spec: 12/12 identical API; intent spec: 10/12 distinct API shapes, 6 field-name schemes | recorded run only | C | no |
| stamp-coupling.md | Fixture: 2/2 stamp sites flagged, control clean; naive mode 22/48 false positives collapse to 0 data-contract | `scripts/probe_stamp_coupling.py` + `_fixtures/stampy` | A | n/a |
| triage-funnel-at-scale.md | SQLAlchemy: 6,342 functions to 797 clusters in 47s; catalogue gate cleared 6/12 (rate 0.50), votes unanimous | recorded run only (detector step reproducible on a SQLAlchemy clone) | C | no |
| ul-boundary-violation.md | Clean null: 0 UL violations in requests, flask, httpie; no non-generic term has 2+ definition sites | `scripts/probe_ul_violation.py` (corpus) | A | n/a |
| volatility-gated-ratchet.md | Gating cut raw flags: requests 9→4, httpie 5→4, flask 7→7 unchanged; zero live-decay misses | `scripts/probe_volatility_ratchet.py` (corpus) | A | n/a |

# Changelog

Output formats are frozen per minor version. Any change to what a command prints requires a minor
bump, because the book reproduces this tool's output verbatim and a reader must be able to tell a
book-tool disagreement from a defect. Install the version the book names.

## 0.6.0 — 2026-08-22

The integrity pass. Every entry closes a gap between what an artefact claimed and what it could
support. Behaviour changes in three places, so this is a minor bump; no printed output moved, and all
fourteen byte-verified manuscript blocks still match.

### Behaviour

- **`selfmodel verify-intent` replaces a check that verified the wrong commit.** The ratification
  policy's `require_signed_commit` ran `git verify-commit HEAD` *before* the intent file was written,
  so the only commit it could inspect was the one before the ratification. A process could ratify on
  top of any signed HEAD and commit the intent unsigned, and the policy passed. Ratify time now says
  where the check lives; `verify-intent` performs it against the commit git reports as the last to
  change the intent file, and checks the signer against the approver allowlist when one is set.
- **`advise --fail-on any` and `gate --fail-on surface` are gone.** Both let a candidate fail a
  build, which the exit-code contract forbids. `advise` accepts `ratified` or `none`; `gate` accepts
  `violation` or `none`.
- **`--rescore` refuses to overwrite scores a different scorer produced.** A superseded run is the
  record of what was claimed at the time, and re-scoring it in place changed the numbers a write-up
  cites without saying so. Pass `--force` to replace them deliberately.

### Added

- **`rescore.json`** beside `scores.json`, binding the committed scores to the scorer that produced
  them. The collection manifest pins the probe as it stood when the responses were bought; a scorer
  corrected afterwards moves that hash without any prompt changing, and conflating the two made a
  sound run read as failing its evidence class. `--verify` now reports `scores_current` separately
  from `probe_changed`, and exits non-zero only on prompt drift or stale scores.
- **`.github/actions/coherence/`** is published with the package. The reusable workflow the book
  prints referenced this path at a tag where it did not exist, because the action lived only in the
  manuscript repository.

## 0.5.0 (unreleased)

### Recorded — the workflows in this tree are inert, and now say so

- **`companion-ci.yml` has never run.** GitHub Actions reads `.github/workflows` at a repository root
  only, and this tree is a subdirectory of the `sdd` monorepo, so the file is a source for the published
  companion rather than a running pipeline. The published `RomanLobus/coherence-ratchet` repo carries its
  own `ci.yml`, whose steps are the tool tests, a quickstart smoke and the compare fixtures: it does not
  exercise `enterprise-seam-lab/` or `formal/` at all. A review and a rectification pass both cited
  `companion-ci.yml` as CI that runs the seam lab, reading the file and not its location.
- `tools/ci-runs-where.tsv` now records, per workflow, where it actually executes and whether it has
  been published, and `tools/ci-artefact-check.sh` fails on a workflow with no such row. An inert file
  that looks like CI is worse than no file, because it gets cited as evidence that something is checked.
- The seam lab was first confirmed locally against pinned oasdiff 1.27.0: it passes end to end, and
  gutting the assertion block in `verify.sh` is refused at the manifest check with exit 1 before
  anything runs. `companion-ci.yml` and both labs were then published to the companion repository,
  where all nine jobs pass, so the seam lab and the formal lab now run on every push rather than only
  on a laptop.
- **Its first ever run found three bugs in the workflow itself**, none of them in the labs: gitleaks
  needs `GITHUB_TOKEN` on pull-request events, the pinned Dafny asset named `ubuntu-20.04` where
  4.11.0 ships `ubuntu-22.04`, and the dogfood job diffs `HEAD~1` against a depth-1 checkout. All
  three are fixed. A workflow nobody runs accumulates defects exactly like a test nobody runs.

### Fixed — a lab's result now names the artefact that produced it

- **`enterprise-seam-lab/manifest.json` hashed the lab's inputs and none of its machinery.** Four
  contracts, two producers and the lockfile were pinned; `verify.sh`, which is the oracle,
  `producer/emit.py`, which chooses the input the recorded verdict is about, the consumer assertion and
  driver, and `package.json` and `tsconfig.json` were not. Inverting the assertion block would have left
  the lab printing "Enterprise seam lab passed." with every recorded hash matching and
  `status: VERIFIED` untouched. Thirteen artefacts are pinned now, split in the manifest into `inputs`
  and `oracle` so the distinction stays visible, with a `source_revision`.
- New `tools/manifest-check.py`, manifest-driven and shared by both evidence labs. Each lab declares its
  own `pins`; `check` refuses a drifted or unpinned artefact and `refresh` is a separate verb, because a
  checker that silently rewrites what it checks is not a checker. Both `verify.sh` scripts call it
  before doing anything, and `companion-ci.yml` gained a tool-free step for it so a drifted oracle would
  fail the pipeline even where oasdiff or Dafny cannot be installed. The idiom is borrowed from
  `experiments/harness/dispatch.py`, which already hashes its own probe source.
- `formal/manifest.json` had the same omission and is fixed the same way.
- **A separate defect the manifest work exposed.** `verify.sh` generated consumer types only from
  `baseline.yaml`, so the book's optional-addition claim, that the consumer still compiles once the
  field is added, was never executed against `optional-addition.yaml`. Compile evidence is now generated
  per contract. Run against both, the consumer compiles, so the claim holds and is now tested.
- `advise.py` emitted `"informationUri": "https://github.com/"` into every SARIF report. It now names
  the repository.

### Added — an optional ratification policy, and an honest limit stated

- **`selfmodel ratify` reads an optional `ratification-policy.json` beside the intent file.** An
  `approvers` allowlist checked against `--by`, and `require_signed_commit`, which asks git whether
  HEAD carries a good signature. Absent by default and silent when absent, so no printed block in the
  book moves and no existing workflow changes. Authority is checked before the model file is read,
  because a refusal is about who is asking.
- **The claim it replaces.** `BOOK-CONTRACT.md` listed "an agent cannot ratify: ratification requires a
  person at a terminal" among the rules the tooling enforces. The second half was false: the command
  requires three non-empty strings, a scope, and a matching model hash, and this repository's own tests
  ratify non-interactively. The contract now separates the rules that are enforced from the one that is
  a convention, the manuscript says so where a reader forms the belief, and "signature" is marked as
  naming a recorded name rather than a cryptographic one.
- `test_an_agent_cannot_ratify` is renamed `test_the_mcp_server_refuses_ratification`, which is what it
  asserts. The old name promised a property the tool does not have, ninety lines below a helper that
  ratifies programmatically.

### Removed — two flags that contradicted the invariant

- **`advise --fail-on any` and `gate --fail-on surface` are gone.** Both made a candidate nobody
  ratified exit 1, which is the one thing the exit-code contract says cannot happen: "A candidate never
  fails a build. Only a line a named person ratified, or a ceiling an owner set, may fail one."
  `advise --fail-on` is now `ratified|none` and `gate --fail-on` is `none|violation`. Neither removed
  value was documented in the manuscript, and neither had a single test, so the capability was
  invisible from every surface a reader or a maintainer reads.
- The reason they survived is worth recording, because it is a lesson about the test rather than about
  the flag. `test_advise.test_there_is_no_option_to_fail_on_a_candidate` asserted
  `set(action.choices) == {"ratified", "any", "none"}`. It read as a guarantee against failing on a
  candidate and was in fact a lock holding `any` in place. It has been replaced by a behaviour test
  that drives every advertised choice through a candidate-only workspace and asserts none of them
  returns 1, which cannot be satisfied by renaming a flag. `test_gate` gained the equivalent.
- `exitcodes.py` now states the predicate it means. It said "A candidate never exits non-zero" and then
  said the candidate is surfaced at 3; three is non-zero, so the sentence was false as written and
  invited exactly the drift below.

### Fixed — the CI artefacts a reader copies

- `.github/actions/coherence/action.yml` **had never been loaded by any parser.** Line 31 carried an
  unquoted scalar containing ": ", and a stray `exit "$code"` sat among the `with:` keys of the
  SARIF-upload step, twenty-four lines below the advise script it belonged to. Both are fixed. The
  second was not cosmetic: without that line the advise step returned 0 for exit 1 (a ratified
  conflict) and exit 2 (a refusal), so the one class permitted to fail a build silently passed.
- `examples/workflows/coherence-minimal.yml` let advise's exit 3 stand as the step's status, which
  turns a surfaced candidate into a red job. It now maps 3 to success explicitly. The chapter 7 block
  that reproduces it was updated in the same edit.
- `.github/workflows/companion-ci.yml` swallowed exit 2. A refusal now fails the job.
- New: `tools/ci-artefact-check.sh`, wired into the regression guard as check 23. It parses every
  shipped CI artefact and executes each advisory run block against a fake CLI at exit 3 and exit 4,
  because both defects above were behavioural and a keyword search would have passed them.


The trust pass. Every entry below is a way the tool could report success while having measured
nothing, which makes the instruction "put `check` in your CI" unsafe to print. Behaviour changes, so
this is a minor bump; no printed output changed, and all seven byte-verified manuscript blocks still
match.

### Behaviour

- **Refusing to measure a tree that is not there.** `measure`, `check`, `init`, `selfmodel derive`
  and `gate` now raise `SourceTreeError` and exit 2 when the source root does not exist, is not a
  directory, or holds no Python files. Previously `os.walk` on a missing path yielded nothing and the
  command returned a complete all-zero snapshot and exit 0, so a renamed directory or a typo in a CI
  invocation made `check` **pass**, and `check --tighten` read the zeros as an improvement and
  ratcheted every ceiling to zero, destroying the budgets file that is the only artefact CI enforces.
- **Refusing the directory that holds the package.** The analyser names a package after the directory
  it is given, so pointing one level up silently measured zero dependency edges — a documented
  footgun in the Quickstart and the getting-started week. Where the root holds no Python files of its
  own and exactly one subdirectory does, the tool now names the subdirectory and exits 2. Verified:
  the loyalty fixture reads 2 dependency edges at the package and 0 at its parent.
- **The pawl declines an empty measurement.** `tighten` refuses every ceiling when a snapshot reports
  zero functions and zero modules. A snapshot carrying neither key is not a whole-tree reading and is
  left alone.
- **`gate` returns an honest exit code.** It returned 0 unconditionally, so a run that surfaced
  uncatalogued divergence, and a run in which the judge was unreachable on every trial, both reported
  success. It now returns 3 for advisory findings, 4 when the judge was asked and never answered, and
  1 only under `--fail-on violation` or `--fail-on surface`. A surfaced cluster is a candidate nobody
  ratified, so it does not fail a build by default.
- **A missing or malformed budgets file is diagnosed, not traced.** `Budget.load` raises
  `BudgetMissing` (naming `init` as the remedy) or `BudgetMalformed` (naming the path), and the CLI
  turns both into exit 2 instead of a raw `FileNotFoundError` traceback.
- **Subcommand registration fails loudly.** Six `try/except Exception: pass` blocks meant an import
  error in any optional module silently deleted a whole verb from the CLI, with every test still
  passing, so the command table printed in Appendix C was unenforced.
- **Python 3.10 is now required.** `requires-python` claimed 3.9, where `sys.stdlib_module_names` does
  not exist; the fallback made the stdlib set empty, so every `import os` counted as a third-party
  dependency and the dependency-sprawl signal inverted. A 3.9 reader got a different number from the
  one printed in the book.

### Added — another tool's counts, so the loop is not limited to Python

- **`import drift <file>`** reads a `drift` baseline or report (github.com/mick-gsk/drift, MIT) and
  writes `coherence/measurement.json` in a new interchange schema, `coherence-measurement/1`, whose
  definition ships at `coherence/measurement.schema.json`. `init --from-measurement` and
  `check --from-measurement` then baseline and hold a line on those counts. The ratify, ground,
  advise and ledger stations already carry no language commitment, so the whole loop now runs
  wherever a producer can export findings — without this project owning a parser per ecosystem.
- **Raw counts only.** An export carrying a composite score and no per-finding records is refused,
  and the message says why: a score falls as the codebase grows while the raw counts hold, which is
  the dilution the pawl exists to refuse. Ratios are computed here and never accepted from a
  producer.
- **Imported findings are candidates, never observations,** with no flag to declare otherwise. The
  producer, its version, and the producer schema version the adapter was written against travel with
  every count, so a grounding pack built on imported facts names the parser that produced them.
- **The adapter is pinned and fails loudly.** It declares which of the producer's schema versions it
  has been read against and refuses any other by number rather than guessing at a mapping. It also
  refuses an export whose declared `finding_count` disagrees with the findings it carries. The
  committed fixture at `_fixtures/interchange/drift-baseline-v1.json` is an excerpt of drift's own
  published baseline, BOM included.
- Every signal the producer reports is watched, rather than the fixed `WATCHED` set. Silently
  dropping the unrecognised ones would baseline a narrower portfolio than the reader believes they
  set. Imported ceilings carry no numerators and need none: a raw count cannot be diluted.

### Fixed

- A subcommand that registered a parser and was never wired into the dispatch table fell out of
  `_main` on a bare `return 2`, printing nothing. A silent exit 2 reads as a usage error the caller
  made. It now names the defect and exits 4, not measured.

### Added — the loop reaches the agent

- **`coherence-ratchet ground`.** `selfmodel context` rendered a grounding pack and nothing consumed
  it, so the loop was open at the join that matters: where what a team ratified reaches the thing
  writing the code. `ground` writes the pack into the files coding agents read — `AGENTS.md` by
  default, since it is the vendor-neutral convention rather than one harness's file — inside a
  managed block delimited by markers, preserving every byte a person wrote outside them. The block
  states its own epistemic contract where the agent will read it: only `[RATIFIED]` lines are
  instructions, `[CANDIDATE]` lines must not be acted on, and frequency is not authority.
- **`ground --check`.** Re-derives the tree and exits 2 when the committed block describes a tree
  that no longer exists. This is the thesis as a build failure: the pull request stops when the file
  the agents read no longer describes the code they are editing.
- **`coherence-ratchet advise`.** Measures a change (`--staged`, `--diff RANGE`, `--patch`, `--stdin`)
  against what the tree already contains and renders a revision instruction. Two finding classes:
  `RATIFIED_CONFLICT`, the only one carrying an imperative, which quotes the approver and the date
  because that is the authority it acts on; and `CANDIDATE_COLLISION`, surfaced and never instructed.
  Default `--fail-on ratified`, so a build fails only where a person already decided. **There is
  deliberately no `--fail-on candidate`**, and the choices assert its absence.
  - A ratification is matched across the whole redundancy family, not only the nearest match.
    Clustering is transitive, so a copy can sit above the threshold against one family member and
    below it against the canonical helper the team actually ratified; a pairwise-only check reported
    the one finding that carried authority as an unratified candidate.
  - Boundary, stated in the module and worth carrying into the book: the detector is structural, so
    it finds a change that *copies* what the tree contains, not a concept reimplemented from scratch
    with different structure. Measured against ten real blind reinventions from a pinned model run,
    it named a collision in none of them (`experiments/advise-detector-boundary.md`): a freshly
    written currency conversion shares almost no shingles with the canonical helper it duplicates in
    meaning. That case is the semantic gate's job, and the flagship detect-and-revise result must not
    be attributed to this command.
  - A diff that cannot be read exits 4, not 0. Reporting "no findings" when nothing was measured is
    the defect this tool exists to name.

### Added — calibration, so the threshold stops being the author's guess

- **`coherence-ratchet calibrate sample|score`, and `--similarity` on `measure`.** `SIM_THRESHOLD`
  was calibrated against the playground fixture and said so, which is honest and not enough: a book
  that withholds the number at the point of decision hands the reader the author's uncertainty rather
  than the author's work.
  - **The sample is stratified across the whole similarity range, including pairs below the current
    threshold.** Sampling only above it makes recall unmeasurable — every pair would already be a
    positive prediction — and an unmeasurable recall is how a precision figure flatters a detector.
    The bands nearest the boundary are over-sampled because that is where the choice lives.
  - **The report recommends nothing.** It prints precision, recall and F1 at every candidate
    threshold with Wilson intervals and the raw counts, names the highest-F1 row and the most
    conservative row reaching precision 0.90, and then stops: precision and recall trade against each
    other, and the trade is a judgement about a codebase and its review capacity, not a computation.
    A test asserts it writes nothing.
  - **It refuses below 100 labelled pairs or 20 positives**, for the reason the ledger has
    `NEEDS_ASSESSMENT`: a number too unstable to act on is worse than an absent one, because it looks
    like evidence.
  - `unsure` is a recorded outcome and is excluded from the figures rather than forced into a class.
    Forcing it is how a ground truth stops being one, and a corpus that was hard to label should say
    so out loud.
  - `calibration/LABELLING.md` ships the rubric, because the labelling *is* the judgement and a tool
    shipped without it would be half the procedure. Its central question is not "are these similar?"
    but "if one needed a behaviour change, would the other need the same change?", with the hard
    cases worked: protocol-mandated similarity, deliberate per-version copies, thin wrappers, and
    same-shape-different-domain.
  - The default is unchanged and passing it explicitly is identical to omitting it, so every block
    the book prints reads exactly as before. Both properties are pinned by tests.

### Added — the grown fixture, and the dilution case it demonstrates

- **`playground/_states/07-checkout-cycle-grown` is now spent.** It was built at ten modules and 297
  lines and then referenced by no test and no chapter, while the sync register listed a chapter-8
  block as pending *because it needed exactly this fixture*.
- **The dilution case is now shown rather than asserted.** Measured against its own smaller twin, the
  grown tree's `cycle_ratio` **falls** from 0.5 to 0.4 while the modules in a cycle **double**, from
  two to four. A ratchet watching the ratio alone would read that as an improvement and tighten its
  ceiling, locking in a structure that got worse. Run against the pawl, the ceiling holds at 0.5 and
  the refusal reads: *cyclic rose 2 -> 4 while the ratio fell 0.5 -> 0.4; the denominator grew, the
  structure did not improve*. A companion test asserts the pawl still tightens on a real improvement,
  so the guard cannot become a ratchet that never moves.
- **`coherence/grown-layering.json`**, a declared layering spec for the ten-module tree. The
  deterministic up-dependency check runs with no API key and catches the `pricing → checkout`
  back-edge. Two tests pin the rule the exit codes encode: a violation of an order a person declared
  can fail a build, and a duplicate cluster nobody ratified cannot.
- The tree carries **two independent cycles** — `pricing ↔ checkout` and `campaigns ↔ discounts` —
  which is what lets one tree be read as two regions with different bars.

### Added — the experiment harness

- **`experiments/harness/`.** Forty-three of the sixty-two experiment write-ups were recorded runs
  rather than re-runnable ones, and the probes were never the problem: several already exposed a
  `build_prompt(condition)` over a committed fixture and a deterministic `score_code(...)` with no
  model in the loop. What was missing was the middle. The dispatcher is written once for every probe
  rather than inside one of them, with a pluggable transport so the same probe can be replicated
  across model families without being touched.
  - **An undated model alias is refused.** A run against `claude-haiku-4-5` is not reproducible,
    because the name points at a moving target and a later comparison silently becomes cross-model.
  - **A failed trial is recorded, never dropped.** Dropping it quietly changes the denominator, which
    is how a sample size lies.
  - **Raw responses are persisted**, so scoring can be re-run offline for ever: a reader without an
    API key can dispute the scorer, and a retired model snapshot does not take the evidence with it.
  - `--rescore` scores persisted responses with no model call; `--verify` reports whether the probe
    or its prompts have changed since the run; `--dry-run` prices a sweep and spends nothing; a
    completed trial is never re-billed on a resumed run.
  - `probe_fullcontext_fragmentation.py` now exposes `CONDITIONS` and `CANONICAL_NAMES`. Both already
    existed under private names; exposing them changes no behaviour and is what makes the run
    re-runnable rather than recorded.
  - Honest promotion count, recorded in `experiments/README.md`: the dispatcher alone reaches about
    twelve write-ups, roughly five more need a scorer written first, the gate experiments need
    committed catalogues instead, and two should not be promoted at all because they use a model as a
    stand-in for a person. A promoted entry stays `RECORDED_RUN` and says *reproducible-as-recorded*,
    never *reproducible*: a sampled model is not a deterministic fixture.

### Added — the agent-facing interface

- **`coherence-ratchet serve`.** An MCP server over stdio, newline-delimited JSON-RPC 2.0
  implemented by hand in the standard library, so the zero-runtime-dependency property survives. It
  is built because the alternative is worse than losing: if an agent in a reader's editor can reach a
  derived-heuristics server and cannot reach the ratified intent, then heuristics instruct the agent
  and the human-approved lines do not — the method inverted, inside the reader's own tooling.
  - It returns **standing**, not findings. `coherence_canonical` answers `RATIFIED` (binding, with a
    typed provenance object naming approver, date, scope, rationale and review date), `CANDIDATE`
    (explicitly not an instruction), or **`NONE`** — a first-class refusal: *there is no canonical
    answer to give you*. Nothing else exposed to an agent can say that, and an agent told nothing is
    approved behaves better than one handed a confident guess.
  - `coherence_exposure` returns the open coherence-debt entries covering a path, with owner, trigger
    and review date. Telling an agent that a region carries accepted debt before it edits a seam has
    no equivalent anywhere.
  - Every response declares whether the model is current, and a stale model **downgrades its own
    epistemic claim** rather than describing a tree that has moved.
  - **Read-only. No tool mutates intent**, and a test asserts the intent file is byte-identical after
    every tool has been called.
  - **`coherence_ratify` is advertised and always refuses**, explaining that ratification requires a
    person at a terminal supplying `--by`, `--scope` and `--rationale`. Advertising the refusal means
    an agent discovers the boundary by reading the tool list rather than inventing a way around one
    it never saw.

### Added — the artefacts a reader copies

- `.github/actions/coherence/action.yml`, `.pre-commit-hooks.yaml`, and
  `examples/workflows/coherence.yml`. Deliberately *not* a detection action: detectors are commodity
  and better resourced elsewhere. The differentiated step is `ground --check`, which fails the pull
  request when the file coding agents read no longer describes the code they are editing.
- The sequence was executed against a real workspace before being written down. On a clean tree
  `ground --check` and `check` both return 0; after a copy-and-diverge lands, `ground --check`
  returns 2 (the grounding went stale), `check` returns 1 (a ceiling an owner set was crossed), and
  `advise` returns 3 (a finding nobody ratified, surfaced and not failing the build). Exit code 4 is
  treated as a failure in the Action, with the reason printed, because a pipeline that green-lights
  on NOT MEASURED has the defect this practice exists to name.

### Added — the catalogue the book prints

- **`coherence/checkout-catalogue.json` now exists.** Chapter 8 printed a gate catalogue and
  `tools/tool-block-sync.md` named this file as the block's authority, and the file was in no tree,
  so the chapter printed an artefact a reader could not fetch and the gate could not read. The
  sync check could not catch it because the row was a *format* row, and a format row is never
  regenerated. The row is now strict and the file is its generator: what the book prints is what the
  gate reads, byte-for-byte after key-order normalisation. Strict blocks go from seven to eight.

### Added

- `coherence_ratchet/exitcodes.py` — the exit-code contract in one place, because the book prints it:
  0 held, 1 crossed, 2 refused, 3 advisory, 4 not measured. Two rules give it meaning: a candidate
  never exits non-zero, and a failure never reads as a clean result.
- `--version`.
- `tests/test_refusals.py` — 14 tests pinning every refusal above, including one asserting the guards
  do not fire on any fixture the manuscript prints numbers for.

## 0.4.0

Nine defects found by cross-reading the tool against the manuscript. Each one is a place where the
shipped behaviour contradicted a claim the book makes, so each is fixed in the tool rather than
hedged in the prose. Every one is pinned by a test.

### Corrected results

- **`compare` no longer compares a function with itself.** Python caches imports by module name, and
  the two sides of a comparison are usually the same package under a before and an after root. The
  second load returned the first root's module, both references resolved to one function object, and
  the comparison reported `NO_DIVERGENCE_FOUND` however far the two had diverged. Verified against
  `x * 100 + 0.5` versus `return 0`, which now refutes with counterexamples. This was a false clear
  on the verification ladder's third rung.
- **`compare` gives each side its own copy of a mutable case.** The seed corpus carries lists and
  dicts, and one object was bound to both sides, so the original mutated the input the replacement
  was about to receive. Two byte-identical functions that append to their argument were reported
  `REFUTED`. Callable strategy cases were already immune; auto-generated cases were not.
- **The pawl keeps the numerator recorded at the baseline when a ceiling holds.** A metric at or
  above its ceiling skipped the decline path and had its numerator refreshed anyway, so a worsening
  could launder itself over two runs: hold the ratio at the ceiling while the count climbs, then grow
  the denominator so the ratio dips, and the pawl tightens against the inflated count. The count
  ended worse and the ceiling ended lower.

### Failures that read as clean results

- **A failed change-history read is reported instead of returning zero.** `git log` failures were
  invisible, because a captured subprocess does not raise, so a path that is not a repository read as
  zero co-changing pairs and the change-history block simply disappeared from the output.
- **Layering judge failures are counted and warned about.** The cluster path records its failed
  trials so an unreachable judge cannot read as an uncatalogued divergence; the layering path
  swallowed them, so a dead judge produced an empty violation list indistinguishable from a clean
  architecture. That is the dangerous direction.
- **A missing or malformed catalogue says so.** A mistyped `--catalogue` path fell through to the
  report for supplying no catalogue at all, and a malformed one died on an unguarded `json.load`
  before the API-key check, crashing even offline. Both now warn, as the layering loader beside them
  already did.

### Accountability

- **`selfmodel query` no longer renders a superseded ratification as live.** The grounding pack
  filtered them; `query` did not, and both print the same `[RATIFIED]` imperative label, so a query
  answered with the superseded revision beside the current one. History stays in the intent file.
- **`check --tighten` records who lowered the ceilings, and when.** The provenance block was copied
  forward from the baseline, so the file named whoever took the baseline and never whoever moved the
  ceiling. A new `tightened` list carries the author, the date, and the metrics moved. `check` gains
  an optional `--by`.
- **`init --force` requires `--reason`.** Only `--by` was checked, while the CLI's own error text,
  the appendix and the honest-metric argument all said the reason was required. Re-baselining is the
  path by which worsening enters without a signed decision.

### Print format

- **The grounding pack names each candidate's sites.** A suggestion carries one canonical home; the
  sites carry every place the concept is currently computed, including those outside the agent's
  window. The pack printed the suggestion alone, which describes the finding without carrying it.

## 0.3.0

The behaviour changes in this release all close gaps between what the book claimed and what the tool
enforced. Every one is pinned by a test.

### Changed behaviour

- **`check --tighten` consults the raw numerator before lowering a ratio ceiling.** A ratio can fall
  because the numerator shrank or because the denominator grew, and under AI authorship the second is
  common. The budgets file now records the numerator standing behind each ratio ceiling, and the pawl
  declines to lower a ceiling whose numerator rose, naming the refusal in the output. A genuine
  improvement in the same run still tightens. Printing the counts beside a ratio was disclosure; this
  is enforcement.
- **The exposure tier rule no longer lets breadth substitute for consequence.** Coordination span and
  blast radius share an evidence base, so breadth alone could supply two of the three highs the count
  clause needed, and one unrelated high would then tip a stable, low-criticality region to `HIGH`. The
  count clause now also requires criticality or volatility to be high. The two named clauses are
  unchanged, so an entry that was `HIGH` through criticality plus coordination span or blast radius
  still is.
- **`report` reads `review_date` for the overdue test**, falling back to a date parsed from the
  repayment trigger. Event-worded triggers carry no date, so reading the trigger text alone left every
  event-triggered entry permanently unchaseable.
- **`init` requires `--by` and refuses to overwrite an existing budgets file without `--force`.** The
  budgets file is the only artefact CI enforces and was the only one with no accountable author. It now
  records author, reason, date, and the ceilings a re-baseline replaced.
- **Ratified intent carries a review date and keeps its history.** A re-ratification retains the prior
  record with a `superseded_by` link and a revision counter instead of discarding it, and the record can
  carry advisers, objections, and a buy-in level. `--scope` is now required: a scope defaulting to the
  whole tree is the over-reach the method exists to prevent.
- **`gate` pins its sampling temperature and reports judge failures as failures.** The multi-trial
  quorum depends on sampling, so the temperature belongs in the code rather than inherited from an API
  default. A trial that errors no longer renders as "no sanctioned pattern reached quorum — uncatalogued
  divergence"; an unavailable or retired judge now says so, and the report carries a `judge_errors`
  count. The conservative disposition is unchanged: a failed trial can never help reach quorum.
- **`gate` warns when a layering spec is missing or unreadable** instead of silently skipping both
  layering checks.

### Added

- **`close`** appends a closing record for a region's open ledger entries. The ledger stays
  append-only, and the report resolves the supersession, so a repaid item stops reading as outstanding
  debt.
- **`check --accept --needs-assessment`** records an entry with a dimension left unassessed, reporting
  the tier as `NEEDS_ASSESSMENT`. Without the flag a partial assessment is still refused with exit 2, so
  the accountable fields stay mandatory.
- **`report --as-of DATE`** makes a run reproducible instead of moving with the calendar.
- **Pinned longitudinal sampling.** `experiments/longitudinal_arch_pins.json` holds sixteen full commit
  hashes per library, and `experiments/data/` holds the measured output, each stamped with the
  analyser's version and hash. Even-index sampling over a growing history is epoch-dependent, so
  without pins the printed digits were not recoverable. `--verify` re-measures against them.
- **A `dev` extra** declaring `pytest`, so the README's development install works.
- **`playground/_states/07-checkout-cycle-grown`**, a state where cyclic modules double while the cycle
  ratio falls, which is what makes the pawl's failure mode demonstrable.

### Fixed

- `report` names a malformed ledger line and skips it instead of failing with a traceback. A
  pretty-printed entry pasted in by hand yields lines that parse as fragments.
- `longitudinal_arch.py` no longer carries an absolute author path or a repository list pointing at a
  dead scratchpad, and it refuses to run against a dirty clone rather than mutating a working tree.

### Compatibility

A 0.2.0 budgets file still loads and still checks. Without recorded numerators the pawl declines to
tighten a ratio it cannot verify, which is the safe direction; re-run `init` to record them.

## 0.2.0

The checkout-pricing fixture, the sync-marker contract for printed blocks, and the guard suite.

## 0.1.0

First public release: the deterministic portfolio, the self-model truth layers, the exposure ledger,
bounded comparison, and the experiment record.

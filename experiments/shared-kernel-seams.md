# Experiment — shared-kernel seam detector (context-map classification)

**Direction:** EXP2. DDD context maps (Khononov, *Learning Domain-Driven Design*, 2021)
classify the seams between contexts. Two are load-bearing for change risk: a **shared
kernel** — a model/type defined in one module and imported by ≥2 others, so a change to
it cascades to every consumer — and an **anticorruption layer (ACL)** — a module that
translates/wraps another's model rather than importing it raw, absorbing change instead
of propagating it. This probe detects shared-kernel seams from the import graph + type
derivation, counts them per repo, and then **tests the risk claim**: are module pairs
joined by a shared-kernel type more co-changing than baseline pairs?

## Operationalisation (deterministic, reuses the shipped package)

- Import graph from `archmetrics._collect_modules` + `_edges_for`.
- A **type** = a top-level class defined in exactly one internal module (its *home*).
  Entity shapes from `selfmodel._explicit_entities` (dataclass/TypedDict/NamedTuple) are
  a subset; widened to all top-level classes because a shared kernel is any shared
  *model*, not only a dataclass.
- **Consumers** of a type = internal modules that import that exact name from its home
  (`from <home> import <Type>`).
- **Shared-kernel seam** = a type with ≥2 distinct consumer modules. Each induces
  consumer-pairs (both joined through the shared type).
- **ACL** heuristic = a module defining an `*Adapter/*Wrapper/*Codec/*Translator/*Mapper`
  class or `to_/from_/adapt/convert` functions. Approximate; reported as a flagged count.
- **Risk test** reuses `probe_hyperliminal.cochange`: for every module pair that
  co-changed ≥1 time, compute Jaccard co-change; compare shared-kernel consumer-pairs
  against all other co-changing pairs (mean/median Jaccard + a rank-sum AUC —
  P(a random kernel pair co-changes more than a random baseline pair); 0.5 = no effect).

## Result — detection is clean; the risk claim is weak and repo-dependent

`scripts/probe_shared_kernel.py`, `git log --all` history, ≥2 consumers:

| repo | modules | single-home types | shared-kernel seams | ACL-ish modules | top kernel (consumers) |
|---|---|---|---|---|---|
| requests | 19 | 46 | **19** | 3 | `Response` (9), `PreparedRequest` (8), `CaseInsensitiveDict` (5) |
| flask | 24 | 44 | **15** | 4 | `App`/`Flask` (7), `Request` (6), `Response` (5) |
| httpie | 78 | 105 | **29** | 9 | `Environment` (21), `ExitStatus` (9), `HTTPHeadersDict` (5) |

The detector lands on exactly the types a maintainer would call the shared kernel:
`requests.models.Response`/`PreparedRequest`, `flask.app.Flask`, `httpie.context.Environment`
(21 consumers — a genuine god-type). These are the highest-cascade change points, found
without any hand-annotation.

**Co-change risk test** (kernel consumer-pairs vs baseline co-changing pairs):

| repo | kernel pairs | baseline pairs | mean J (k / b) | median J (k / b) | P(kernel > baseline) |
|---|---|---|---|---|---|
| requests | 58 | 110 | 0.036 / 0.052 | 0.033 / 0.036 | **0.42** |
| flask | 85 | 178 | 0.097 / 0.087 | 0.078 / 0.070 | **0.55** |
| httpie | 155 | 693 | 0.155 / 0.096 | 0.069 / 0.043 | **0.61** |
| **pooled** | **298** | **981** | **0.115 / 0.089** | **0.060 / 0.045** | **0.565** |

Read honestly: the risk claim holds only weakly and only in the aggregate.
- **requests: negative/null** (AUC 0.42) — shared-kernel pairs co-change *less* than
  baseline. Its kernel types (`Response`, `PreparedRequest`) are stable public API; the
  churn is elsewhere. A clean counter-example.
- **flask: null** (AUC 0.55, means within noise).
- **httpie: weak-to-moderate positive** (AUC 0.61, mean J 0.155 vs 0.096) — its shared
  kernel *does* co-change more, consistent with the cascade claim.
- **Pooled AUC 0.565** — a real but small effect: a shared-kernel pair beats a random
  baseline pair only 56.5% of the time (50% = coin flip). This is a nudge, not a law.

## What it means for the method

- **Shared-kernel detection is a strong, cheap steward signal on its own.** "This type is
  imported by N modules; a change here cascades to all N" is exactly the blast-radius
  warning the book wants at the merge decision — and it is computed from the import graph
  with no history and no LLM. Rank types by consumer count; the top few *are* the
  contexts' shared kernel.
- **The co-change risk claim does not generalise as stated.** Static fan-in (how many
  modules import a type) and empirical co-change (how often modules change together) are
  only weakly related here. The strong-form claim — "shared-kernel seams are the
  co-changing hotspots" — is falsified in requests and null in flask; only httpie
  supports it. The correct claim is the *static* one (cascade potential), not an
  empirical co-change one.
- Complements hyperliminal coupling (RES1), which is the *opposite* quadrant: high
  co-change with **no** import edge. Shared kernel is high import fan-in; whether it also
  co-changes is, per this data, mostly not.

## Honest limits

- **"Shared type" is a heuristic approximation of a shared kernel.** A DDD shared kernel
  is a *deliberately shared model between teams*; here it is any class imported by ≥2
  modules, which conflates true domain models (`Response`, `Environment`) with utilities
  (`CaseInsensitiveDict`, `HTTPHeadersDict`). No team boundaries exist in these repos to
  separate the two.
- **ACL detection is approximate** — name/verb heuristics (`*Adapter`, `to_/from_`). It
  finds `requests.adapters`, `httpie ...adapters`, but cannot confirm a module actually
  *translates* a shared model versus merely being named that way. It is not used in the
  risk test, only reported.
- **Small-n and stable libraries.** n = 3, Python-only, all well-factored public libraries
  whose shared kernels are frozen public API — the population least likely to show
  cascade churn. The effect could be larger in fast-moving multi-team application code.
- Co-change granularity is coarse (squash/refactor commits inflate pairs); `--no-merges`
  only partly mitigates.

## Verdict

Shared-kernel seams are **detectable and useful as a static blast-radius signal**: the
probe cleanly identifies the highest-fan-in model types per repo (19 / 15 / 29 seams;
`Response`, `Flask`, `Environment`) with no annotation. But the **risk claim that these
seams are also the co-change hotspots is weak and repo-dependent** — negative in requests,
null in flask, weakly positive in httpie, pooled AUC 0.565. Report it as a null-to-weak
empirical result. The defensible contribution is the static seam classifier, not a
co-change law.

**Proposed claim (honest strength — *weak / static-only*):** "A type imported by ≥2
modules is a shared-kernel seam whose change cascades to every consumer; a steward can
rank cascade risk by consumer count directly from the import graph. Whether such seams
also co-change more than baseline is, in these libraries, at best a weak effect (pooled
AUC ≈ 0.57) and sometimes reversed — so treat consumer-count as the risk proxy, not
observed co-change."

→ book: add shared-kernel fan-in (consumer count per type) to Ch.6's signal set as a
static blast-radius measure beside dependency cycles; do **not** claim it predicts
co-change. Note the ACL/context-map framing (Ch.3 structure-spec) as the conceptual home,
and flag ACL auto-detection + team-boundary data as the engineering gaps.

## Artefacts

- `scripts/probe_shared_kernel.py` — reuses `archmetrics` (import graph, class extraction) and
  `probe_hyperliminal.cochange` (co-change); stdlib-only, `git log --all`.

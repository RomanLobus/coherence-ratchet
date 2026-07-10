# Experiment — ubiquitous-language / bounded-context violation (null / low-yield)

**Direction:** EXP3, extending the entity-coherence signal. Khononov (*Learning
Domain-Driven Design*, 2021): within a bounded context each term should have "one and
only one meaning." A **ubiquitous-language violation** is the same domain term — an
entity/class/type name, or a dict-shape "kind" — resolving to *structurally divergent
shapes* in different modules **without an intervening translation**: the KeyError-class
interoperability break, where module A builds a `Foo` with one field set and module B
reads a `Foo` with an incompatible one and no adapter reconciles them.

Where `experiments/entity-coherence.md` studied one entity fragmented across an
*independent-agent* codebase (5 incompatible `Order` schemas), this looks at *established*
codebases: group every entity/dict shape by normalised name, flag names with ≥2
incompatible field/key sets living in different modules, and check for a translation on
the path.

## Operationalisation (deterministic, reuses the shipped package)

- Shapes from `selfmodel._explicit_entities` (dataclass/TypedDict/NamedTuple: name +
  fields + module) and `selfmodel._dict_shapes` (implicit dicts: base name + per-site key
  sets).
- Group by **normalised name** (lowercased, plural-stripped).
- **Exclude generic container names** — `kwargs/options/self/data/params/headers/result/
  context/...` — because a dict called `kwargs` holding different keys in two modules is
  two unrelated local option bags, not one shared term with two meanings.
- **Violation** = a non-generic term in ≥2 modules with ≥2 structurally incompatible
  shapes (neither field set a subset of the other).
- **Translation check** = is any involved module ACL-ish (`*Adapter/*Wrapper/*Codec` class
  or `to_/from_/adapt/convert` functions)? If so, the divergence is mediated, not a break.

## Result — clean null across all three repos

`scripts/probe_ul_violation.py`:

| repo | candidate domain terms | terms in ≥2 modules | **UL violations** |
|---|---|---|---|
| requests | 2 | 0 | **0** |
| flask | 0 | 0 | **0** |
| httpie | 18 | 0 | **0** |

**Zero violations, and the reason is structural, not a threshold artefact:** in these
libraries *no non-generic domain term is defined in more than one module at all.* Every
entity type has a single home (`Response` lives only in `requests.models`;
`Environment` only in `httpie.context`) — the same property that makes the shared-kernel
detector (EXP2) work. With one definition site per term, there is nothing to diverge.

The only names that *did* appear with divergent shapes across modules were generic
containers, correctly excluded:
- requests: `headers` (`adapters` vs `sessions` — different HTTP header keys).
- flask: `options` (`app` / `templating` / `sansio.app`), `kwargs` (`helpers` / `testing`).
- httpie: `kwargs` (4 modules, 4 key sets), `self` (`config` / `sessions`).

None is a domain term. `kwargs` carrying `max_help_position` in one module and
`ssl_version` in another is not "one term, two meanings" — it is two unrelated local
option bags that happen to share Python's keyword-argument idiom. Flagging them would be
a false positive; the generic filter is doing exactly its job.

## Explicit overlap with the entity-coherence probe

This probe **substantially overlaps** the entity-coherence signal and adds little on this
population, exactly as anticipated:
- Both consume the same raw material (`_explicit_entities` + `_dict_shapes`).
- entity-coherence asks: *is a single entity fragmented into incompatible shapes?*
  (measured on an independent-agent codebase, where it fired 5/5).
- This probe asks the same question keyed on *term name across modules* — but in
  well-maintained libraries the precondition (a domain term with ≥2 definition sites)
  never occurs, so it fires 0/3.

The distinct contribution over entity-coherence is only the **translation-mediation
check** (does an ACL sit between divergent sites?) and the **generic-name filter**.
Neither earns its keep here because there are no divergent domain-term sites to test them
on.

## Why the null is the honest and expected finding

Single-maintainer OSS libraries with a settled public API are the *least* likely place to
find ubiquitous-language violations: one author, one mental model, one definition site per
type, reviewed merges. The violation this probe targets is a **multi-team brownfield**
pathology — team A's `Customer` (billing fields) and team B's `Customer` (CRM fields)
colliding at an integration seam with no ACL, producing the KeyError/failed-validation
break entity-coherence demonstrated under the independent-agent condition. That condition
is absent here, so the detector correctly reports nothing.

## Honest limits

- **n = 3, Python-only, single-maintainer libraries** — the population where a null is
  most expected. This is *not* evidence the signal is worthless; it is evidence these
  repos are coherent (a valid, if unexciting, measurement).
- **Term-name grouping is shallow.** Two modules could model the same concept under
  *different* names (`Customer` vs `Client`) — a real UL violation this probe misses
  entirely. It only catches the same-name/different-shape case.
- **The generic-name list is a hand-curated heuristic.** Too aggressive and it hides real
  domain terms that happen to be common words; too lax and `kwargs` floods the output.
  Tuned here toward precision (no false positives) at the cost of possibly excluding an
  edge-case domain term.
- **ACL/translation detection is approximate** (name/verb heuristics) and untested here
  because no violation reached that stage.

## Verdict

**Null / low-yield result, reported as such.** Across requests, flask and httpie the
ubiquitous-language-violation probe found **0 violations**, because no non-generic domain
term is defined in more than one module — these libraries are coherent by construction. On
this population the probe adds little over the existing entity-coherence signal (same raw
material, stricter precondition that never triggers). The signal is real and demonstrated
elsewhere (entity-coherence, 5/5 under the independent-agent condition); it simply does
not bite in well-maintained single-team code. It would bite in multi-team brownfield code
where the same term is owned by different teams — which is precisely the book's target
setting, and where this probe (plus a cross-name synonym pass) would earn its place.

**Proposed claim/refinement (honest strength — *null here; conditional elsewhere*):** "The
same domain term resolving to incompatible shapes in different modules without a
translating adapter is a ubiquitous-language violation and a KeyError-class break. In
well-maintained single-team libraries this is absent (0/3 repos: every domain type has a
single home) — so it is a *brownfield / multi-team* signal, not a general one. A steward
should run it at integration seams between team-owned sub-packages, and pair it with
synonym detection (same concept, different name) to catch the case name-matching misses."

→ book: keep domain-model coherence as a Ch.6 signal (per entity-coherence), but frame the
*cross-module term-collision* variant as a **brownfield/multi-team** check, not a
universal one; note it overlaps entity-coherence and that its value is the translation
gate + team-boundary scoping. Name synonym detection (concept-level, not name-level) as
the open extension.

## Artefacts

- `scripts/probe_ul_violation.py` — reuses `selfmodel._explicit_entities` + `_dict_shapes` and
  `archmetrics._collect_modules`; stdlib-only, generic-name filter + ACL/translation gate.

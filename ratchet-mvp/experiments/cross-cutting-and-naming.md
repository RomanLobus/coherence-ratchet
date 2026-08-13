# Experiment — Cross-cutting-concern & naming coherence (two more facets)

**Why:** continuing the facet sweep beyond the dependency graph and the domain model. Two more axes of architecture coherence: are *cross-cutting concerns* (logging, error handling) done one way or many across modules, and is the *vocabulary* for the same concept consistent? Same two-part test: do independent agents fragment them, and does the detector catch it?

**Result: both fragment, with a subtle and important twist — the high-level *choice* can converge while the *conventions* fragment underneath it. Five agents all chose stdlib `logging`, yet diverged on level, message format, exception base class, and validation; and named the same actor four different ways. The detector caught both cross-cutting and naming inconsistencies in 5/5 trials, and correctly passed the genuinely-consistent items.**

## (a) Fragmentation — five user-management tasks, independent agents

| Axis | Result |
|---|---|
| Logging *library* | **converged** — 5/5 used module-level `logging.getLogger(__name__)` |
| Logging *conventions* | **fragmented** — success level DEBUG vs INFO (2); message format key=value vs dotted-prefix vs prose (3) |
| Error handling | **5/5 distinct** — custom exc vs `ValueError` subclass vs bare `ValueError`; attribute-rich vs bare; validation on some, none on others |
| Exception base class | 2 (some `Exception`, one `ValueError`) — no shared "catch a domain error" base |
| Entity name for the same actor | **4 distinct** — Customer / User / UserAccount / Credential |
| Identifier name | 3 — `customer_id` / `user_id` / `account_id` (+ `username`) |
| Retrieval/removal verb | varied — fetch / get / remove / delete |

The twist: **convergence at the top can hide fragmentation underneath.** All five agents picked the same logging library — a strong shared prior — so a shallow look says "logging is consistent." But how they *used* it (levels, formats) and everything around it (exception taxonomy, validation, vocabulary) fragmented. Coherence drift lives in the conventions, not just the headline choice.

## (b) Detection — multi-trial

| Metric | Result |
|---|---|
| Trials catching a cross-cutting inconsistency | 5/5 (5–6 findings each: log level, message format, exception base, constructor, validation) |
| Trials catching a naming inconsistency | 5/5 (identifier name, entity name, verb) |
| Trials catching **both** | **5/5** |
| Correctly marked genuinely-consistent items as consistent | yes — the logger-acquisition idiom (variants=1), the WARNING level on failures, and raise-on-missing-entity (with the list-query's empty-result correctly judged a *justified* difference, not an inconsistency) |

The detector did not just flag everything — it distinguished the consistent (logger idiom, failure level, the deliberately-different collection-query return) from the inconsistent (levels, formats, exception taxonomy, vocabulary). Precision and recall both held on a multi-faceted fixture.

## What it means
- **Cross-cutting and naming are real coherence facets, and they fragment under independent AI authorship** — error handling completely (5/5 distinct), vocabulary heavily (4 names for one actor), logging *conventions* even when the library choice agreed.
- **The "convergence masks fragmentation" finding is a caution for any shallow coherence check.** A metric that only checks "is everyone using the logging module?" would pass; the incoherence is in the levels, formats, exception taxonomy, and names. This is why the semantic detector matters — it reads the conventions, not just the imports.
- **The detector generalises to these facets too, with good discrimination.** Same two-stage idea; here the semantic pass did the work (there is little deterministic floor for "is logging used consistently"), and it correctly separated real drift from justified difference — the steward-actionable output the method wants.

## Honest caveats
- Toy (5 tasks, one domain), Claude/Python, generated-clean, detector saw all modules in one context (the scale wall again).
- No-shared-convention condition (independent agents) — the upper bound; a team with a house style fragments less. The contribution is that the facets fragment and detection catches them, plus the convergence-masks-fragmentation nuance.
- "Distinct error approaches = 5/5" is by the agents' own labels; the detector's grouping is the cross-check, and it agreed there is real inconsistency.

## Verdict
Cross-cutting-concern consistency and naming/vocabulary coherence are two further facets of architecture coherence that AI fragments and the two-stage detector catches (5/5 on both, with correct discrimination of consistent-vs-inconsistent). The notable finding is that *high-level convergence can mask convention-level fragmentation* — a shallow check is fooled, a semantic one is not. Combined with entity coherence, this establishes the pattern across facets: AI fragments whatever convention is not shared, and the detector reads it.

→ book: Ch.6 signal set widens again — cross-cutting consistency (logging/error/auth) and ubiquitous-language/naming drift join dependency cycles and entity divergence; Ch.7 detector remit; the "convergence masks fragmentation" caution belongs in the dead-ends/limits thread (a shallow consistency check passes while the conventions drift). Same scale/context caveat as all the LLM-detection facets.

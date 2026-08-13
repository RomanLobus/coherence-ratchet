# Dependency sprawl — single-use third-party imports as a candidate drift lens

**Motivation.** SIG's Sigrid benchmark names "libraries introduced for a single use and never cleaned up" as part of the AI drift signature, beside the duplication and naming divergence the portfolio already watches (Software Improvement Group, 2026 — vendor observation; GitClear's corpus findings point the same way). The existing dependency signals read the *internal* import graph only; this mode is invisible to them. R11/F6; Claim 55.

**Operationalisation.** From the package's import statements: third-party = imported top-level names that are neither stdlib nor internal modules. A dependency is **single-use** when exactly one module of the package imports it. Churn = distinct third-party count at first-parent history samples. Implemented in `coherence_ratchet.signals` (surfaced in `measure` as an informational section, never ratcheted) + `probe_dep_sprawl.py`.

**Results (flask / requests / httpie, at HEAD):**

| repo | distinct third-party | single-use | churn (oldest → newest samples) |
|---|---|---|---|
| flask | 9 | 6 (asgiref, blinker, cryptography, dotenv, itsdangerous, markupsafe) | 4 → 8 → 23 → 12 → 14 → 14 |
| requests | 8 | 3 (OpenSSL, certifi, simplejson) | 0 → 53 → 22 → 25 → 14 → 10 |
| httpie | 10 | 6 (charset_normalizer, colorama, defusedxml, importlib_metadata, multidict, requests_toolbelt) | 2 → 4 → 7 → 5 → 8 → 10 |

**Verdict — mechanics validated; the count alone is not a drift verdict.** Mature, well-maintained libraries *do* carry single-use imports, and reading the names shows why: they are deliberate single-purpose integrations (itsdangerous for session signing, certifi for CA bundles, defusedxml for safe XML), not abandoned bloat. Requests' churn series is the instructive one — 0 → 53 (the vendored-dependency era) → 10 (after deliberate cleanup): the *trend* carries the story the snapshot cannot. So the lens is a **triage list a person reads with history**, not a gate and not a score: on AI-era application code the same list is where "imported for one call in March, never touched again" shows up, and the churn series is what separates a curated footprint from an accreting one.

**Proposed claim (honest strength):** single-use third-party imports are deterministically countable and the churn series is readable from history [measured — mechanics]; the *drift* reading is conditional on context the count does not carry (deliberate integration vs abandoned bloat), so the lens is informational triage, with its expected bite on AI-era application code rather than curated libraries [vendor-named mode; first-party mechanics only].

**Limits.** Libraries ≠ applications (small, curated footprints by design); import-statement parsing misses dynamic imports and extras; "third-party" classification is heuristic (stdlib list + internal-name exclusion); churn samples are first-parent snapshots, not a full series; n=3 repos, Python only.

# Experiment — stress-response consolidation heuristic (RES4)

**Direction:** RES4 (Residuality). Barry's incidence matrix: components with the **same stress response**
(identical rows) "live and die together" and can be combined to reduce N. Operationalised as: modules
whose *change response* is near-identical — very high co-change (Jaccard ≥ 0.5) — are module-merge / boundary
candidates. Distinct from code-duplication (P1), connascence (P3), and function-cluster co-change (P2): it
flags modules that **always change together whether or not they share code**.

## Result

`scripts/probe_stress_response.py` (J ≥ 0.5, co ≥ 3):

| repo | combine-candidates | of which NOT import-linked |
|---|---|---|
| requests | 0 | 0 |
| flask | 0 | 0 |
| sqlalchemy | 0 | 0 |
| **httpie** | **7** | **5** |

httpie's `rich_utils / rich_help / rich_palette / man_pages` form a de-facto **module family** that
co-changes at J = 0.6–0.75 with **no import edges between most of them** — a consolidation/boundary
candidate that *no code-similarity signal would surface* (they are not code-duplicates; they are a feature
cluster that always evolves together). The well-factored/small libraries trigger none at this threshold.

## What it adds to the method

- A **co-evolution consolidation dimension**: organise modules by how they change, not only by code
  similarity. Feeds the combined priority score (P9 / claim 33) at the *module* level — "these belong
  together (merge or draw an explicit boundary)" — which the duplication/connascence signals miss.
- Converges with RES1 (the same `rich_*` family shows up as hyperliminal coupling); RES4 reframes those
  high-co-change hidden families as **combine candidates**, RES1 as **hidden-coupling warnings** — two
  readings of one signal.

## Honest caveats
- Sparse: only httpie fired at J ≥ 0.5; the signal needs enough shared history and is thresholded.
  Small/well-factored codebases (requests, flask) show none — correctly.
- "Combine" is a *suggestion to a steward* (merge, or make the implicit family an explicit module), not an
  automatic move — and "always co-change" can be a feature-area artefact, not a true merge case.
- Overlaps RES1; the distinct contribution is the module-level "reduce N" framing, not a new detector.

## Artefacts
- `scripts/probe_stress_response.py` — reuses `probe_hyperliminal` (co-change + static graph).

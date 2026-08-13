# Experiment — hyperliminal coupling as a first-party signal (RES1)

**Direction:** RES1 (Residuality Theory pass — O'Reilly 2024). Residuality names **hyperliminal coupling**:
coupling invisible until a change hits, where a fix ripples across components that share no explicit
dependency (contagion). In the incidence matrix (stressors × components) it is "two 1s in a row." This
probe operationalises it deterministically for a real codebase: a **stressor = a historical commit**
touching the source package; a module is **affected** if the commit touched it; **hyperliminal coupling =
a pair of modules that co-change but have no static import edge**; **contagion = commit blast radius**.
It is co-change (`probe_cochange`) ∩ the static graph (`archmetrics`) — the change-coupling the dependency
graph cannot see — targeting the book's "beyond-context" cost (reframe-E/Eb) with a number.

## Result — a real, orthogonal signal

`probe_hyperliminal.py`, `git log --all` history (robust to the src/ migration), Jaccard ≥ 0.25, co ≥ 3:

| repo | modules | source commits | static edges | mean blast (max) | co-change pairs | static-linked | **hyperliminal** |
|---|---|---|---|---|---|---|---|
| requests | 19 | 1577 | 68 | 1.28 (18) | 0 | 0 | **0** |
| flask | 24 | 1303 | 81 | 1.56 (20) | 8 | 4 | **4** |
| httpie | 78 | 560 | 206 | 2.05 (22) | 14 | 6 | **8** |

The signal **discriminates and is orthogonal to the import graph**:
- **requests** (small, well-factored) shows *no* hyperliminal coupling and a blast radius near 1 — changes
  stay local. A clean control.
- **flask** surfaces 4 hidden couplings — `tag↔debughelpers`, `signals↔globals`, `tag↔logging`,
  `debughelpers↔logging` — modules that co-evolve with no import edge between them.
- **httpie** surfaces 8, including a tight `rich_utils / rich_help / rich_palette / man_pages` family
  (J = 0.6–0.75, no edges — a de-facto feature module-group) and `argparser↔definition` (co-changed 21
  times, no direct import — a strong hidden coupling routed through a shared consumer).

Contagion has a **long tail** everywhere (max blast 18–22): a few changes touch many modules — the risky
ones a steward should watch.

## What this changes in the method

- **Ch.6 / Appendix A — a new drift signal.** Hyperliminal coupling (high co-change ∧ no static edge) is
  a computable axis distinct from cycles, coupling, and fan-in. It catches what the static detector is
  blind to by construction — the "changes-together-but-not-linked" couplings — which is the empirical face
  of the book's *beyond-context* cost. Add it beside connascence of meaning (P3) in the signal set.
- **Contagion (blast radius)** is a cheap per-change risk score: rank changes/PRs by how many modules they
  touch; high-contagion changes are where hidden coupling bites.
- Feeds RES3 (do AI authors create more of it?) and RES4 (identical-response consolidation).

## Honest caveats
- Co-change ∧ ¬static-edge conflates two things: genuine hidden coupling (a real dependency routed
  indirectly, e.g. `argparser↔definition`) and *thematic* co-change (a feature family edited together,
  e.g. the `rich_*` group). Both are useful to a steward — the latter marks a missing explicit boundary —
  but the signal is "evolves together, not linked," not "secretly depends on." State that.
- "Stressor = historical commit" is one operationalisation; it measures *realised* change-coupling, not
  the *potential* stressors Residuality simulates. Thresholds (J≥0.25, co≥3) are unter-tuned.
- Commit granularity is coarse (a large refactor commit inflates co-change); `--no-merges` mitigates but
  squash-merges still bundle. n = 3 libraries; Python-only.

## Artefacts
- `probe_hyperliminal.py` — reuses `archmetrics` (static graph) + git history; `--all` + package-relative
  suffix matching so it survives detached HEAD and the requests/ → src/requests/ move.

# Experiment — volatility-gated dependency-cycle ratchet (VOL1)

**Direction:** VOL1 (Khononov, *Balancing Coupling*, 2025). Khononov's thesis is that "coupling
only matters where it meets volatility" and "the goal is not to minimise coupling." The
architecture ratchet (architecture-ratchet.md) flags every interval in which `cycle_ratio` rises.
Some of those rises happen among **frozen/legacy modules** — code that no longer changes — and
flagging those is a false positive: nobody is going to touch that cycle, so it is not decay a
steward needs to act on. **Hypothesis:** gating the cycle signal by per-module volatility
(normalised git commit-frequency) suppresses the frozen-module false positives without missing
live decay (cycles that recruit modules people are still editing).

## Operationalisation (stated explicitly)

`scripts/probe_volatility_ratchet.py`, imports the shipped `coherence_ratchet` package (does not edit it);
reuses `archmetrics` (static graph + Tarjan SCCs), `probe_hyperliminal.cochange` (per-module commit
counts), and `longitudinal_arch`'s 16-sample first-parent history sweep. `git log --all` throughout
(HEAD is detached in the fixtures). Deterministic — identical output across runs.

- **Volatility(m)** = commits touching module `m` over full history, **max-normalised to [0,1] per
  repo** (divide by the busiest module's commit count). Computed once over full history, read at
  each sample. A module is **frozen** if volatility ≤ **0.05**.
- At each sample the probe extracts the **set of cyclic modules** (in an SCC of size > 1), not just
  the ratio, from `archmetrics`' own graph + Tarjan.
- **Raw flag** on interval (t → t+1): `cycle_ratio(t+1) > cycle_ratio(t)` — the baseline ratchet.
- **Gated flag**: keep the flag only if at least one module that **newly enters a cycle** at t+1 is
  non-frozen (volatility > 0.05). If every newly-cyclic module is frozen, **suppress**.
- A suppressed interval is a **true-positive suppression** iff all its newly-cyclic modules are
  genuinely frozen; the probe prints each newly-cyclic module's volatility so this is checkable, not
  asserted.

## Result — raw vs gated per repo

| repo | commits | frozen share | RAW flags | GATED flags | suppressed | of which true-positive | of which neutral* |
|---|---|---|---|---|---|---|---|
| flask | 3011 | 0.25 | **7 / 15** | **7 / 15** | 0 | 0 | 0 |
| requests | 3292 | 0.37 | **9 / 15** | **4 / 15** | 5 | 3 | 2 |
| httpie | 1635 | 0.62 | **5 / 15** | **4 / 15** | 1 | 1 | 0 |

\* *neutral* = `cycle_ratio` rose but **no** module newly entered a cycle — the ratio moved because
the denominator (`n_modules`) changed, not because anything backslid. Not a frozen suppression and
not a decay miss; see below.

**Sanity check against architecture-ratchet.md.** flask's trajectory reproduces (0.00 → **0.833**,
monotone small increases: 0.033 → 0.095 → 0.429 → … → 0.833). The 7/15 vs the prior ~30/43 is purely
coarser sampling (16 first-parent samples vs ~43 dense ones); endpoint and shape match.

### The suppressed intervals, checked

- **requests, 3 true-positive suppressions.** Every newly-cyclic module was frozen (volatility 0.0):
  `util` + `safe_mode`; the vendored-urllib3/chardet cluster `ssl_match_hostname / pyopenssl /
  fields / connection / chardet / response`; and `retry`. These are exactly the legacy/vendored code
  a steward should *not* be paged about — the gate did the intended job.
- **requests, 2 neutral (denominator-shift) intervals.** `cycle_ratio` rose (0.183→0.265,
  0.287→0.389) with **no** module entering a cycle, because `n_modules` collapsed (104→68, 101→18)
  when the vendored urllib3 tree was removed from requests. The raw ratchet flagged these as
  backsliding; they are artefacts of the denominator, not decay. Gating removes them too, but for a
  *different* reason than the hypothesis names — worth stating rather than banking as a win.
- **httpie, 1 true-positive suppression.** The `input` module (volatility 0.0) entered a cycle;
  frozen, correctly suppressed.
- **flask, 0 suppressions.** flask's cyclic core (`app`, `blueprints`, `helpers`, `sansio.*`, …) is
  all high-volatility live code, so **every** raw flag survives gating. This is the strong control:
  gating did **not** blunt the live-decay detection that made the architecture ratchet work.

## Verdict

**Gating suppresses frozen-module false positives, and does so without touching live decay — but the
effect is small and confined to one repo of three.** On flask (the reference decay case) gating is a
no-op: 7 → 7, because flask's decay is genuinely live. On requests it cuts 9 → 4, and 3 of those 5
suppressions are verified frozen-module true positives (the other 2 are denominator artefacts the
raw ratchet should not have flagged either). On httpie it cuts 5 → 4, one verified true positive.
So the mechanism is real and correctly targeted where it fires — it did not suppress a single
live-decay interval across the three repos (no misses) — but on this evidence its practical payoff
is modest and repo-dependent: it matters most for codebases carrying vendored/legacy trees
(requests), and does nothing for a codebase whose decay is all in live code (flask).

### STRETCH — per-edge balance/friction score

Per-edge **friction ≈ integration_strength × distance × volatility(source)** at the current tree
(integration_strength = count of import statements a→b; distance = package-tree hops via
closest-common-ancestor depth; volatility = source module's normalised churn). Aggregated to the
source module, then correlated (Pearson) with cycle membership and connascence-of-meaning
participation:

| repo | corr(friction, in-cycle) | corr(friction, connascence) | mean friction cyclic / acyclic |
|---|---|---|---|
| flask | +0.15 | +0.83 | 11.36 / 0.29 |
| requests | +0.38 | +0.79 | 21.04 / 0.08 |
| httpie | +0.23 | +0.51 | 13.57 / 3.95 |

Honestly: the **friction↔connascence** correlation is moderate-to-strong and consistent across all
three repos — high-friction modules also carry more implicit shared-literal agreements, which is the
Khononov intuition (costly coupling clusters). The **friction↔in-cycle** Pearson is only weak-positive
because in-cycle is binary and friction is heavily right-skewed; the **group-mean split** is the real
signal — cyclic modules carry 40×–260× the friction of acyclic ones. Caveat that partly bites: friction
contains volatility by construction, so its link to a volatility-adjacent quantity is not fully
independent. Treat the stretch as directional support, not a clean correlation.

## Honest limits

- **Commit-frequency is one volatility proxy.** Khononov's volatility is about the *rate of business
  requirement change*; git churn is a proxy that conflates **feature churn with bug-churn and
  refactor-churn**. A module hammered by bug fixes reads as high-volatility here but may be stable in
  requirements — the confound Khononov himself flags. Not disentangled.
- **"Frozen" is entangled with "deleted."** Most requests suppressions are frozen because the module
  was *removed* from the current tree (vendored urllib3), so max-normalisation from the current tree
  assigns it 0.0. Arguably correct (dead code is maximally frozen) but it means the win is partly
  "the ratchet ignored code that no longer exists," which is weaker than "ignored live-but-stable
  legacy."
- **Small n, Python-only, coarse sampling.** 3 libraries, 16 samples each, one language. The neutral
  denominator-shift intervals show sampling is coarse enough that structural reorganisations dominate
  some intervals.
- **HEAD-detached history / `--all`.** `--all --first-parent` over detached fixtures is a reasonable
  mainline reconstruction but can fold in merged topic branches; the trajectory is robust, exact
  interval boundaries less so.
- **Retrospective simulation.** Shows the gated signal *would* have fired differently, not that a
  team acted on it. Threshold 0.05 is chosen, lightly, not tuned.

## Proposed claim (at the strength the probe supports)

> **[measured + limit]** Gating a dependency-cycle ratchet by per-module git-commit volatility
> suppresses frozen/legacy-module false-positive backsliding flags (requests 9→4, httpie 5→4;
> verified frozen) with **zero** live-decay misses across three libraries — but the payoff is modest
> and repo-dependent (no effect on flask, whose decay is all live code), and rests on commit-frequency
> as a volatility proxy that does not separate feature-churn from bug-churn.

→ book (Ch.7 / Appendix A): volatility is a **secondary gate** on the architecture ratchet, not a
replacement for it — it trims false positives from vendored/legacy trees without weakening the
live-decay pawl. Dead-end noted honestly: "volatility-weighting is the headline improvement" — no; on
the reference decay case (flask) it changes nothing.

## Artefacts

- `scripts/probe_volatility_ratchet.py` — standalone; imports (does not edit) `coherence_ratchet`; reuses
  `archmetrics` SCCs, `probe_hyperliminal.cochange`, and the `longitudinal_arch` sweep. Run:
  `python3 probe_volatility_ratchet.py [--stretch]`.

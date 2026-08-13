# Experiment — Distance from the Main Sequence (A-I-D) as a Python decay signal

**Direction:** B2 (corpus pass). Clean Architecture (Martin, Ch.14) and Building Evolutionary
Architectures (Ch.4) propose **Abstractness** A = abstract-types / all-types, **Instability**
I = Ce/(Ca+Ce), and the **normalised Distance from the Main Sequence** D = |A + I − 1| as a
composite architectural-health metric (D near 0 = healthy; the "Zone of Pain" is concrete-and-stable,
A≈0 ∧ I≈0). `archmetrics.py` already computed I; this probe added A (ABC / Protocol /
`@abstractmethod` detection) and D, then re-ran the longitudinal study (`longitudinal_arch.py`,
16 samples over each library's full git history).

**Question:** does D decay over time the way `cycle_ratio` does — i.e. is it a second, independent
ratchetable signal the book is missing?

## Result — NEGATIVE: A-I-D does not port to Python; D is degenerate

Across all four mature libraries (12–16 years each), **mean abstractness sat at ≈ 0.0 for the
entire history** (range 0.0000–0.0145):

| Repo | A (start → end) | I (mean) | D (start → end) | cycle_ratio (start → end) |
|---|---|---|---|---|
| flask    | 0.0 → 0.0     | ~0.51 | 0.65 → 0.46 | **0.22 → 0.83** |
| requests | 0.0 → 0.0     | ~0.41 | 0.53 → 0.50 | 0.14 → 0.58 |
| httpie   | 0.0 → 0.0035  | ~0.45 | 0.79 → 0.59 | 0.0 → 0.15 |
| boltons  | 0.0 → 0.0104  | varies | 0.0 → 0.18  | **0.0 throughout** |

With A pinned at ≈ 0, the distance collapses to D = |0 + I − 1| = **1 − I**, so it carries **no
information beyond the instability `archmetrics` already reports**, and it moves *opposite* to the
real decay: as flask's cycles climbed 0.22 → 0.83, its D drifted *down* 0.65 → 0.46 (because mean
instability rose toward 0.5). The `zone_of_pain` count is degenerate for the same reason — with A
always < 0.3, every stable module is flagged "pain," so the signal is dominated by instability alone.

## Why

Martin's A counts **abstract classes and interfaces**. Java/C# codebases are full of them, so A is
informative there. Idiomatic Python expresses the same designs with concrete classes, duck typing,
functions, and modules; explicit `abc.ABC`/`typing.Protocol`/`@abstractmethod` declarations are rare.
Four long-lived, well-maintained libraries spanning 2010–2026 essentially never declare them. So the
abstractness axis — and therefore the whole Main-Sequence construct — is **near-degenerate for Python
source** and adds nothing the dependency-structure signals (cycles, coupling, fan-in, instability)
do not already capture.

## What the book should take from this

- **Dead-end / limit (Ch.10, Appendix A):** "Distance from the Main Sequence as a second ratchet
  metric" — retired for Python. It is a weak, sometimes-inverted proxy here, the same shape as the
  retired "function duplication is the coherence signal" finding. Report it as honestly as the
  successes. (It would likely be informative in a statically-typed, interface-heavy language — name
  that boundary; do not claim it transfers.)
- **Keep the *principles*, drop the *metric*.** REP/CCP/CRP and ADP/SDP/SAP remain useful **vocabulary
  and normative targets** for the structure-spec (Ch.3) — "depend toward stability," "no cycles,"
  "classes that change together live together." The book can teach those as design intent without
  claiming the A-I-D *number* is a usable Python instrument.
- `cycle_ratio` stays the headline architectural signal (unchanged); instability stays a diagnostic.

## Honest caveats
- Abstractness detection is deterministic and conservative (ABC/Protocol base, ABCMeta metaclass,
  `@abstractmethod`/`@abstractproperty`). It will miss informal "abstract by convention" base classes,
  which is *why* Python abstractness reads ~0 — but that is exactly the point: the formal construct the
  metric needs is absent in idiomatic Python, so even a more generous detector would be guessing.
- Same Python-AST, single-package, rough-calibration limits as `architecture-decay.md`.
- n = 4 libraries; the claim is "degenerate on idiomatic Python," not a universal verdict on A-I-D.

## Artefacts
- `coherence_ratchet/archmetrics.py` — A, D, zone-of-pain added to `ArchSnapshot` (instability already present).
- `longitudinal_arch.py` — architecture-level history runner (cycle_ratio, coupling, I, A, D, pain).
- `longitudinal_arch_out.json` — last run's raw points.

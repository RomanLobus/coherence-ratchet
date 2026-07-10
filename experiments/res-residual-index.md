# Experiment — residual index as an outcome metric (RES2 / RES2b)

**Direction:** RES2 (Residuality Theory pass — the flagship). Residuality's standout instrument is the
**residual index Ri = (Y − X) / S**: apply a fresh battery of S stressors to a *naïve* architecture
(survives X) and a *treated* one (survives Y); Ri > 0 means the treatment raised
survivability-under-change. The book measures *structure* (cycles, duplication) but has no *outcome*
metric for whether coherence actually pays. This probe adopts Ri as that outcome metric: does a
**coherent** subsystem survive cross-cutting change better than a **fragmented** one, when an AI maintainer
makes the change?

## Design
Two versions of a checkout-pricing subsystem computing an order total. **Fragmented:** the total is
computed in three (RES2) then four (RES2b) structurally-divergent places, each with its own tier-rate
table and rounding. **Coherent:** one canonical `pricing.order_total`; all sites delegate. Battery of
stressors = cross-cutting change tasks: S1 add a log line (local control), S2 add a PLATINUM tier, S3
switch to banker's rounding, S4 honour a per-line `discount_exempt` flag, S5 add shipping. An AI maintainer
attempts each on each version (n=1/cell). **"Survived"** = an oracle the agent never sees: for probe orders
exercising the stressor, all sites return the same value **and** it equals the expected-correct total
(enforces feature-present *and* cross-site consistency). RES2b buries a fourth total site
(`analytics/report.py`) among 24 decoy modules so the agent must discover it.

## Result — Ri = 0 in the discoverable regime

| variant | sites | stressors | fragmented X | coherent Y | **Ri** |
|---|---|---|---|---|---|
| RES2 (fully visible) | 3 | S1–S5 | **5/5** | 5/5 | **+0.00** |
| RES2b (4th site buried in 31 modules) | 4 | S2,S3,S5 | **3/3** | 3/3 | **+0.00** |

The coherent version survived by delegation (one edit to `order_total` propagates everywhere). But the
**fragmented version survived just as often** — the agent diligently updated all three (RES2) and all four
(RES2b) divergent sites every time, *including the site buried among 24 decoys*, which it found by search.
For PLATINUM it updated three/four separate rate tables; for rounding, three/four `quantize` calls; for the
exempt flag, it rewrote three separate loops. Coherence made **no difference** to survivability.

## What this means — the honest, calibrated finding

This is not a failed null. It is a **replication of the book's own reframe-E/Eb finding, now with an
outcome metric**: a search-capable AI maintainer threads a cross-cutting change through fragmented code as
reliably as through coherent code **so long as the divergent sites are discoverable** — even buried among
decoys (RES2b), because the agent greps and finds them (exactly P7). So:

- **The survivability payoff of coherence is ~0 for the AI maintainer in the discoverable regime.** It
  appears only when a divergent site is **genuinely undiscoverable** (jargon-named / beyond reach — the
  boundary P7 pinned) or when the reader is the **bounded human** (the open human-review study).
- This **tempers, not strengthens, a naive "coherence pays" claim**, and it does so in the book's own
  honest register. It reinforces the calibrated thesis (Ch.12): the cost of incoherence concentrates at
  the seams and beyond-context sites, not in navigable internal fragmentation.
- It sharpens the **economics** (Ch.5/Ch.9): don't over-invest coherence effort where a search-capable
  agent copes anyway; spend it at the contract seams and where discoverability fails — a direct argument
  for the entropy budget and "just enough governance."

## Method upgrade delivered
The **residual index is adopted as a first-party outcome instrument** (survivability under a fresh stressor
battery), alongside the structural signals. Its first reading is a calibrated result, not a slogan:
Ri ≈ 0 for AI maintainers where sites are discoverable; the coherence dividend is conditional. → Ch.1/2
(the thesis gains an outcome test), Ch.5/9 (economics), Ch.12 (where coherence pays), Appendix C.

## Honest caveats
- n = 1 per cell; toy 3–4 site fixtures; Claude + Python. Directional.
- "Survived" is a strong oracle (agreement == expected); the *coherent* arm survives partly by
  construction (delegation), and the *fragmented* arm's survival came from the agent reading carefully and
  updating every site — the same "safety from diligence, not structure" seen in P8.
- Ri is Barry O'Reilly's instrument for *design-time* survival of *business* stressors; adapted here for
  *maintenance* survival of *change* stressors under AI authorship — an adaptation, not Residuality as
  intended.
- The positive-Ri regime (undiscoverable site) is established by reference to P7 (jargon-named helper
  reinvented at any size), not re-run here; a jargon-named 4th site is the natural RES2c follow-up.

## Artefacts
- `scratchpad/res2/` (coherent, fragmented, judge.py, 10 trials) and `scratchpad/res2b/` (hidden 4th site
  among decoys, judge2.py, 6 trials).

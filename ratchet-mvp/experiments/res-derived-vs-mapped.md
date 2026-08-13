# Experiment — derived vs hand-mapped structure-spec survivability (RES6)

**Direction:** RES6 (Residuality's anti-prediction challenge, engaged as a probe). O'Reilly's sharpest
critique of structural methods: "being faithful to an abstraction that cannot keep up with the rate of
change is a common cause of architectural failure" — mapped structure rots. Book 2's central artefact is a
structure-spec / self-model, so the critique lands on it directly. This probe tests it. A subsystem
computes the order total at **four** sites (`checkout`, `receipt`, `revenue`, and `analytics/report`, the
last added after the map was written). An agent applies a cross-cutting stressor **at the sites the spec
lists**:
- **stale hand-mapped spec** — lists only the 3 original sites (the map went stale when the 4th was added).
- **fresh derived spec** — regenerated from code, lists all 4.

Three stressors (PLATINUM tier, banker's rounding, shipping). "Survived" = the 4-site oracle (all sites
agree and equal the expected total).

## Result — derivation removes the staleness failure mode

| spec | survived | failures |
|---|---|---|
| **fresh (derived)** | **3/3** | — |
| **stale (hand-mapped)** | **1/3** | S3 rounding: sites `[502,502,502,505]` (4th still half-up); S5 shipping: `[4597,4597,4597,3998]` (4th missing shipping) |

The stale-map failures are precisely the drifted 4th site diverging because it was not on the map. The
one stale *survival* (S2) came from an agent that **noticed the map was stale, read the code, found
`analytics/report.py`, and updated it anyway** — flagging the discrepancy explicitly. Two other stale
agents deferred to the map (one even wrote: "not in the spec, so I left it unchanged … the spec is now
stale").

## What this settles for the book — the anti-prediction tension, answered

- **Barry's critique is real and reproducible:** agents faithful to a stale hand-map miss the drifted
  site (2/3 here). A hand-maintained structure-spec rots exactly as Residuality warns.
- **The book's design choice survives it — because the self-model is *derived*, not hand-maintained.**
  The fresh/derived spec (regenerated and bound to the tested source revision) survived 3/3. This turns O'Reilly's
  critique into **evidence for reframe-A**: freshness-by-derivation is not a convenience, it removes a
  measured failure mode. Ch.3 should argue derived-over-mapped on *survivability* grounds, not only
  "never goes stale" in the abstract.
- **Honestly bounded:** a capable agent *sometimes* catches the staleness by reading code (stale_S2), so a
  stale map is not always fatal — but survival then depends on agent diligence (the P7 "agents search"
  effect, the P8 "safety from diligence" effect). Derivation removes that dependence. The claim is
  "derivation eliminates the failure mode," not "a hand-map always fails."

## Where it lands
- **Ch.3** — the survivability case for the *derived* self-model over a hand-authored spec.
- **Ch.10** — dead-end: "a hand-maintained structure map" (it rots; agents follow it off a cliff).
- **Ch.12** — co-position with Residuality: the book agrees mapped structure rots, and answers it by
  deriving the map rather than abandoning structure (Barry's conclusion). Honest engagement of a
  respected contrarian.

## Honest caveats
- n = 1 per cell (3 stressors × 2 conditions); the stale/fresh split is 1/3 vs 3/3, directional not a rate.
- The effect is partly instruction-mediated (agents told the spec is authoritative); a fully autonomous
  agent might search regardless (as stale_S2 did). That variance *is* the point — derivation removes it.
- Adaptation of Residuality's argument to a maintenance artefact, not Residuality as intended.

## Artefacts
- `scratchpad/res6/` — `spec_stale.md`, `spec_fresh.md`, 6 trials; judged with `res2b/judge2.py`.

# Experiments — contagion (RES3) and criticality stopping-rule (RES5)

Two Residuality primitives assessed against data already gathered, honestly bounded.

## RES3 — do AI authors create more hyperliminal coupling / contagion?

**Primitive:** contagion = a change's blast radius; hyperliminal coupling = hidden co-change (RES1).

**The clean measurement is blocked, and the reason is on record.** A direct AI-vs-human comparison of
hyperliminal coupling over git history needs *aged, AI-authored* codebases; those do not yet exist at
sufficient history (established in `longitudinal-decay.md` / `architecture-decay.md` — the same wall the
macro decay curve hits). So RES3's clean form is design/open, not runnable now.

**What can be said, first-party and bounded:**
- **Contagion scales with the number of divergent sites.** In the RES2/RES2b/RES6 fixtures a cross-cutting
  change had to touch 3–4 modules in the fragmented version and 1 in the coherent one — a 3–4× blast
  radius. RES1 measured real-repo contagion directly (httpie mean blast 2.05, tail to 22).
- **RES6 shows contagion becomes *failure* under imperfect visibility:** when the blast radius exceeds
  what the map (or the agent) covers, a site is missed and the change diverges (stale-spec 2/3 failures).
- **AI's established additive, low-consolidation bias** (Mao 2026; Huang/Horikawa 2026) *increases the
  number of divergent sites over time*, so it raises future contagion and the odds of a missed site —
  **indirectly**. That is the defensible link: AI does not need a new coupling mechanism; it multiplies
  the sites a change must reach.

**Verdict:** contagion ∝ fragmentation is first-party (RES1/RES2); "AI raises contagion" holds only as a
consequence of the established fragmentation bias, with the direct longitudinal test blocked by the young
age of AI codebases. Log as bounded, not a new measurement. → Ch.2/Ch.6 (contagion as the cost of
fragmentation), honest-limits (the direct curve awaits aged AI systems).

## RES5 — criticality as a stopping rule for the entropy budget

**Primitive:** "looping" — when fresh stressors are already survived, the architecture is at criticality;
iterating drives the residual index Ri → 0 (diminishing returns).

**Result, anchored on RES2:** the coherent subsystem **survived every stressor** in the RES2 battery
(Ri over the fragmented version = 0 in the discoverable regime) — i.e. it was already **at criticality**
for that battery: new cross-cutting changes were absorbed without further structural work. The fragmented
version was not (each stressor demanded N-site edits).

**The method upgrade:** this gives the entropy budget (Ch.5) and the integrator (Ch.9) a **measurable stop
condition** they currently lack — iterate the residual index over fresh stressors and *stop consolidating
when marginal Ri → 0* (fresh changes are already survived). It answers "how much coherence is enough?"
with a criterion rather than taste, and operationalises "just enough governance" (B4): reaching
criticality, not perfection, is the goal (Barry: "the goal of the architect is criticality, not
correctness" — kin to the book's "safe is not good").

**Honest caveats:** RES2's battery is small (5 stressors), so "at criticality" here means "survives this
battery," not a proof of general criticality; a true stopping rule needs a broad, evolving stressor set
(the same modelling-choice caveat as RES2). This is a conceptual mapping + the RES2 anchor, not a
multi-round iteration experiment. → Ch.5 (budget stop rule), Ch.9 (when to stop the integrator).

## Artefacts
- Uses `probe_hyperliminal.py` (RES1 contagion) and the `res2`/`res2b` residual-index results.

# Experiment: the semantic gate on the `requests` clusters

**Question.** The deterministic detector finds near-duplicate clusters but cannot
tell *decay* (should consolidate) from *sanctioned symmetry* (leave alone). Can a
multi-trial LLM gate make that call — and do it consistently?

**Method.** The 8 redundancy clusters the detector found in `requests` (dunders
excluded), each judged by **5 independent LLM trials** under a forced schema
(`CONSOLIDATE` / `SANCTIONED` / `UNSURE` + reason + confidence), framed as an
objective classification, majority-voted, scored against hand-labelled ground
truth. 40 judges total. Built the way the deep-research pass said it must be:
multi-trial, objective framing, majority vote — not a single subjective verdict.

## Result

| Cluster | Members | Human label | Gate verdict | Votes | Match |
|---|---|---|---|---|---|
| C1 | get/patch/post/put | SANCTIONED (certain) | SANCTIONED | 5/5 | ✓ |
| C2 | session + api verbs | SANCTIONED (certain) | SANCTIONED | 5/5 | ✓ |
| C3 | md5/sha/sha256/sha512_utf8 | **CONSOLIDATE (certain)** | SANCTIONED | 5/5 | ✗ |
| C4 | _find / _find_no_duplicates | SANCTIONED (ambiguous) | SANCTIONED | 5/5 | ✓ |
| C5 | iterkeys / itervalues | SANCTIONED (likely) | SANCTIONED | 5/5 | ✓ |
| C6 | list_domains / list_paths | CONSOLIDATE (ambiguous) | SANCTIONED | 5/5 | ✗ |
| C7 | is_permanent_redirect / is_redirect | SANCTIONED (likely) | SANCTIONED | 5/5 | ✓ |
| C8 | from/to_key_val_list | SANCTIONED (ambiguous) | SANCTIONED | 4/5 | ✓ |

- **Mean trial agreement: 0.97** — near-unanimous on every cluster.
- **6/8 match the human label; 2/3 on the clear-cut anchors.**
- **The gate predicted SANCTIONED for all 8.** It never once said CONSOLIDATE.

## What it actually shows

1. **Consistency is not correctness.** The gate was *unanimously* (5/5),
   *confidently* (high) wrong on C3 — the clearest consolidation candidate, four
   copies of one hash helper. High agreement gave false reassurance, exactly the
   "a cue can inflate consistency while making it systematically biased" failure
   the literature warns about. Multi-trial voting fixed the *flip-rate* worry and
   did nothing for the *bias* worry.

2. **The gate has a strong "leave it alone" bias.** 6/6 correct on genuinely
   sanctioned clusters, **0/2 on genuine consolidation candidates.** As a decay
   detector it never fired. As a gate it would block nothing and miss everything
   it was built to catch.

3. **The "wrong" answer is defensible — the line is a judgement, not a fact.**
   The C3 reasoning ("four distinct hash algorithms required by different
   digest-auth directives, mirroring an external protocol") is arguable. A
   reasonable engineer could call C3 sanctioned. The label itself is contestable,
   which is the deeper point: *whether a duplicate is decay is a judgement call*,
   and consensus among judges cannot make it authoritative.

## Implication for the method

The semantic layer's job is **not** to decide CONSOLIDATE vs SANCTIONED
autonomously — on real code it is biased to "sanctioned" and confidently wrong on
real candidates. Its reliable, demonstrated strength is the *other* direction:
**clearing intentional symmetry** (6/6). So the defensible architecture is:

> deterministic detector finds near-duplicates → the LLM layer **suppresses the
> obviously-sanctioned ones** (high precision, multi-trial) → a human steward
> judges the short residue and owns the consolidate call.

The LLM is a **noise filter between the detector and the human**, not the
decision-maker, and it must **surface, not gate** (auto-blocking would miss the
very candidates that matter). This matches the deep-research verdict — LLM
judging is reliable for the narrow objective task and unreliable for the
subjective "should this be consolidated?" — and now it is confirmed on real code.

## Caveats

- n = 8 clusters, one library, one judge model family, low reasoning effort.
- Ground truth for C3/C6 is contestable (that is part of the finding).
- C8's `to_key_val_list` source was a typing `@overload` stub (extraction
  artefact), so that input was degraded.
- A fairer test of the *intended* role would frame the task as "is this clearly
  intentional symmetry — yes/no?" and measure how well it shortens the human's
  review list, rather than asking it to make the consolidate decision.

## Re-test: the sanction-clearing framing

The fairer test, run. Same 8 clusters, same 5 trials, but the task was reframed
to the gate's *intended* role: **CLEAR** (confidently intentional — safe to
dismiss without a human) versus **REVIEW** (surface to a human). The prompt told
the judge to be conservative — "when in doubt, REVIEW; it is cheap to send a
borderline cluster to a human and costly to dismiss a real duplicate" — and a
cluster was only cleared on a 4-of-5 consensus.

It failed harder.

| metric | result |
|---|---|
| dangerous false-clears (real candidates dismissed) | **2 / 2** (target 0) |
| obvious symmetry auto-dismissed | 4 / 4 |
| human review list | reduced from 8 to **0** |
| all real candidates surfaced | **no** |

The gate cleared **all eight** clusters — including both genuine consolidation
candidates (C3 the four hash helpers, C6 the two list accessors), 5/5 each, high
confidence. The "when in doubt, REVIEW" instruction did nothing, because the
model was never in doubt: it confidently rationalised every cluster as
intentional, even acknowledging for C3 that "consolidating into one parameterised
function would be possible" before clearing it anyway. The conservative 4-of-5
quorum was inert because the votes were unanimous.

**Two framings have now failed.** Asking the LLM to judge intentionality — in
either direction — does not work on this fixture. A likely confound sharpens the
point: `requests` is famous, and the judges repeatedly cited it by name ("the
canonical public API of requests…"). The familiarity/reputation prior the
literature documents (judges favour low-perplexity, canonical-looking code) shows
up live as "this well-known library must be deliberate." A gate that clears
duplication *because the code looks established* is precisely backwards for
catching decay.

**What this leaves.** The deterministic detector plus a human steward is the part
that survived both experiments. The semantic layer did not earn an autonomous
seat. One variant remains untested and is the method's actual design: give the
gate the project's **explicit pattern catalogue** and ask the *objective* matching
question — "does this cluster match catalogued sanctioned pattern X? cite it" —
rather than asking it to judge intentionality from its own priors. That is the
regime the research said LLM judging is reliable in (objective fact-matching,
Kappa 70–86). Both experiments here tested the subjective regime, and both
failed. The catalogue-matching variant is the semantic layer's last credible
shot; until it is shown to work, the book should present the LLM layer as
*unproven* and lean the method on the deterministic ratchet and the human.

## Catalogue-matching test: the variant that works

The method's actual design, finally tested. Instead of asking the LLM to judge
intentionality, it was given an explicit catalogue of four sanctioned `requests`
patterns (http-verb-wrapper, dict-interface-mirror, response-status-property,
cookie-lookup-variant) and the *objective* question: "does this cluster match one
of these named patterns, or NONE?" — the regime the literature says LLM judging is
reliable in. The catalogue deliberately did not bless a "family of helpers
differing only by a swapped primitive" shape (C3) or a "per-attribute accessor"
shape (C6). Same 5 trials, same conservative 4-of-5 quorum to clear. No hint about
which clusters should fail to match.

| metric | result |
|---|---|
| dangerous false-clears | **0 / 2** (target 0) |
| correct disposition (right pattern, or correctly NONE) | **8 / 8** |
| real candidates surfaced to a human | **yes** |
| human review list | reduced from 8 to **3** |

The same C3 hash-helper cluster that both subjective framings confidently cleared
now returned NONE 5/5, with precise reasoning ("no catalogue entry describes
hash-digest helper families… parametric clones, the opposite of
cookie-lookup-variant's intent"). C1/C2 matched http-verb-wrapper 5/5, C4
cookie-lookup-variant, C5 dict-interface-mirror, C7 response-status-property. C6
split 4 NONE / 1 (one trial tried to stretch dict-interface-mirror to fit), and
the conservative quorum correctly sent it to review — the multi-trial design
earning its keep on the one ambiguous case.

## Conclusion across three experiments

The three runs triangulate one finding cleanly:

1. Subjective "should this consolidate?" — failed (confidently wrong on C3).
2. Subjective "is this safe to dismiss?" — failed harder (cleared everything, 2/2
   dangerous), even told to be conservative.
3. Objective "does this match a catalogued pattern?" — worked (0/2 dangerous, 8/8
   correct, candidates surfaced).

**The mechanism that flips the result is the catalogue, not the model.** Asked to
judge intent from its own priors, the LLM rationalises any structural similarity
in familiar code as deliberate. Forced to point at a specific human-blessed
pattern or return NONE, the burden of proof flips and genuine duplicates fall
through to a human. So the semantic layer earns a *qualified* seat: an objective
matcher against an explicit, human-curated catalogue — never an autonomous judge
of intent. Its reliability is borrowed from the catalogue's quality, which is
exactly why the catalogue (the externalised design memory) is the load-bearing
artefact and the human steward owns it.

Open caveats: n = 8, one library, one model family; `requests` is familiar to the
model (the familiarity prior that hurt experiments 1–2 may have helped here), so
the decisive next test is an unfamiliar or proprietary codebase. But the
mechanism — objective catalogue-matching beats subjective judgement — is the
generalisable result, and it is what the deep-research pass predicted.

## Replication on a less-familiar codebase (boltons)

The familiarity caveat, addressed. The catalogue-matching test was repeated on
`boltons` — a real but less-canonical utility library — with a deliberately
adversarial twist. `boltons` vendors an `OrderedMultiDict`: `urlutils` holds a
byte-identical copy of `dictutils`' methods, a duplication the model may well
"know" is intentional. The catalogue was given only two sanctioned patterns
(dict-interface-mirror, decorator-closure) and **no vendoring pattern**, and the
prompt told the judge to ignore outside knowledge and match only against the
catalogue. Six clusters, five trials each.

| metric | result |
|---|---|
| dangerous false-clears (vendored copies wrongly cleared) | **0 / 2** |
| correct disposition | **6 / 6** |
| catalogue constrained the model | **yes** |
| human review list | reduced from 6 to 4 |

The identical `dictutils.add ↔ urlutils.add` and `pop ↔ pop` copies returned NONE
5/5 — surfaced for review, not cleared — with the model explicitly declining to
invoke boltons' vendoring convention: "identical cross-module duplication matching
neither stated intent should be flagged for human review." The two genuinely
sanctioned clusters (a dict-interface mirror, a decorator closure) matched their
patterns 5/5 and cleared.

This closes the caveat that mattered most: on a less-familiar codebase, with a
catalogue that deliberately withheld the convention the model could have appealed
to, the gate respected the catalogue's boundary rather than its own prior. The
objective-matching mechanism holds, and the catalogue — not the model — is what
does the work.

# Experiment — the constrained catalogue-matcher, made runnable

**Why this exists.** `gate-generalisation.md` recorded the gate disposing every cluster correctly
across three libraries with no dangerous false-clear. Its catalogues and its ground-truth labels were
never committed, so the figure stayed `RECORDED_RUN`, and on 22 August 2026 Appendix C stopped printing
it. This is the experiment that could be built in its place: the surviving framing, run against the
committed cluster fixture (`_fixtures/gatejudge/`) and the reconstructed catalogue
(`coherence/catalogues/requests-catalogue.json`), whose own `_note` says a run against it "is a new
experiment with its own date, not a replication of the old one".

It is a new experiment. It does not confirm the old figure and is not offered as doing so.

**Design.** Eight clusters, five trials each, two dated model snapshots. The prompt supplies the
cluster bodies and the catalogue, names the catalogue as the only authority, and asks for one exact
entry name or NONE. `probe_gate_catalogue.py` scores two things separately, and keeping them apart is
the whole design.

## Result

`claude-haiku-4-5-20251001` and `gpt-5.4-2026-03-05`, 5 trials × 8 clusters × 2 families, 2026-08-22.
Every response and a manifest committed under `data/runs/gatecatalogue/`.

| Measure | haiku | gpt |
|---|---:|---:|
| Responses returning an exact catalogue entry or NONE | **40/40** | **40/40** |
| Invented pattern names | **0** | **0** |
| Unparseable responses | **0** | **0** |
| Clusters cleared | C1 only, 5/5 | C1 only, 5/5 |
| Cleared a cluster the labels marked CONSOLIDATE | **0** | **0** |

**The claim this carries, and the half that needs an oracle.** Constrained to a catalogue, the gate
stayed inside it. Across eighty trials on two families it never invented a pattern name: every answer
was an exact catalogue entry or NONE. That half is a property of the output alone, checkable against
the catalogue file with no judgement about which clusters deserved clearing, and it is the half the
design was chosen for.

The second figure is not of that kind and should not be reported as though it were. "Never cleared a
cluster the labels marked for consolidation" is computed against `ground_truth` in the fixture
(`probe_gate_catalogue.py`, `cleared_against_label`), so it inherits whatever those labels are worth,
and they are one rater's with no written rubric. It does not err safe in both directions either: a
cluster wrongly labelled as safe to leave would hide a clear that should have counted against the
gate. The number is a descriptive comparison against a weak oracle, not a safety property, and no
claim about dangerous clears rests on it.

**The claim this does not carry.** Raw agreement with the hand labels is 20 of 40 per family, and the
number is a coverage artefact rather than a gate error. The reconstructed catalogue holds three
patterns; six clusters are labelled SANCTIONED. Five of those six have no catalogue entry, so the gate
correctly returns NONE and the label comparison scores it as disagreement. A gate cannot clear what the
catalogue does not contain, and it should not. Read the agreement column as a measurement of catalogue
coverage.

The labels also carry the limitation recorded above `CLUSTERS` in `probe_gate_judge.py`: one rater, no
written rubric. Nothing here reports a disagreement with them as an error.

## Honest limits

- One library, three catalogue patterns, eight clusters, five trials a cluster. A catalogue of
  hundreds of entries, fine-grained distinctions, and genuinely ambiguous candidates are untested.
- The catalogue is reconstructed, so this measures the framing and not the original run's stimulus.
- Zero dangerous false-clears over eighty trials bounds the rate loosely, not tightly; the Wilson
  upper bound at n=40 per family is not small.
- Temperature 1.0, matching the sibling probe, so the run measures the framing under sampling rather
  than a greedy decode.

## Reproduce

    python3 experiments/harness/dispatch.py --probe probe_gate_catalogue --trials 5 \
      --model claude-haiku-4-5-20251001 --out experiments/data/runs/gatecatalogue/<date>-haiku-4-5

    python3 experiments/harness/dispatch.py --probe probe_gate_catalogue \
      --rescore experiments/data/runs/gatecatalogue/<date>-haiku-4-5

Rescoring needs no key and no network.

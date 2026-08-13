# Experiment — the derived-versus-stale-map result does not reproduce single-shot

**Direction:** `res-derived-vs-mapped.md` answers Residuality theory's sharpest critique of
structural methods, that a mapped abstraction rots. Its figures, a fresh derived spec surviving 3/3
stressors against a stale hand-map's 1/3, are quoted in Chapter 12's graveyard table and in its
prose. Three trials is the weakest sample behind any figure the manuscript prints, so it was the
first candidate for promotion out of `RECORDED_RUN`.

**It did not promote. Two harnessed designs, 140 trials, and neither reproduced the effect.** The
reason is specific and it is worth more than the promotion would have been.

## What was run

A four-site fixture ships at `_fixtures/derivedmap/`: four modules that each compute an order total,
with the fourth, `orders/analytics/report.py`, added after the map was written. The change is a new
loyalty tier. The oracle is the original's: every site carries it.

Twenty trials per arm, `claude-haiku-4-5-20251001`, deterministic scorer, every response committed.

| Arm | What the agent had | Oracle |
|---|---|---|
| `no_spec` | all four files' source, no spec | **20/20** |
| `stale_map` | all four files' source, spec listing three | **20/20** |
| `derived_spec` | all four files' source, spec listing four | **20/20** |
| `hidden_stale` | three files' source, spec listing three | **0/20** |
| `hidden_derived` | three files' source, spec listing **four** | **0/20** |

## Why it did not reproduce, in two parts

**With every file visible, the spec cannot matter.** All three visible arms scored 20/20. An agent
that can read `analytics/report.py` updates it whether or not a document mentions it, so a stale map
costs nothing. This is the book's own visibility finding arriving where it was not wanted: the
instrument could not detect a map effect because visibility had already saturated the outcome.

**With the file hidden, naming it is not enough.** The interesting arm is `hidden_derived`. The spec
named `orders/analytics/report.py` explicitly, and in twenty trials out of twenty the agent returned
only the three files whose source it had been shown. Naming a site an agent cannot read does not get
that site changed. A derived spec's advantage over a stale one requires the agent to be able to act
on the name, which in a single-shot prompt it cannot.

## What this does and does not say about the original

It does not refute it. The original ran in a session where the agent could read files it had not been
handed, and that is the regime where a spec naming an unseen site pays: the name is actionable
because a read follows it. This harness is single-shot by construction, so it removed the mechanism
the original was measuring.

What it does establish is that the quoted figures are **regime-dependent in a way the write-up did
not state**. Chapter 12's graveyard table cites them as evidence that derivation beats a hand-map;
that holds where an agent can fetch what the spec names, and this run shows it does not hold
otherwise. The claim needs its regime attached wherever it appears.

## A first fixture that could not test its own hypothesis

The first version of the fixture had all four sites delegate to one shared rate table. Every agent
in every arm correctly edited that single file, and all three arms scored 20/20 before any of the
above was run. A subsystem whose sites share a table is immune to a stale map, because the correct
change is one edit; testing staleness needs the divergence that makes staleness cost something. The
fixture was rebuilt with four divergent implementations, which is what the original described.

That failure is recorded rather than quietly fixed because it is the example-conformance gate doing
its job: a fixture must exhibit the phenomenon it claims to test, and this one did not until it was
made to.

## Status

`res-derived-vs-mapped.md` stays `RECORDED_RUN`. The promotion needs a harness with tool-use, so the
agent can read a file the spec names, which is the regime the original occupied and this one does
not reach.

## Reproduce

    export SSL_CERT_FILE=$(python3 -c "import certifi;print(certifi.where())")
    python3 experiments/harness/dispatch.py --probe probe_derived_vs_mapped.py \
        --condition no_spec --condition stale_map --condition derived_spec \
        --condition hidden_stale --condition hidden_derived \
        --trials 20 --model claude-haiku-4-5-20251001 --max-tokens 3000 \
        --out experiments/data/runs/derivedmap/<date>
    python3 probe_derived_vs_mapped.py --tally experiments/data/runs/derivedmap/<date>

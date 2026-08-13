# Experiment — telling an agent to reuse changes nothing it can already see

**Direction:** `prevention-reuse-or-justify.md` produced the book's most-cited negative result: with
the canonical helper already visible in context, adding a reuse-or-justify instruction moved reuse by
nothing at all. Chapter 12 quotes that figure in the graveyard table, and Chapter 2's argument that
visibility rather than willingness drives reinvention rests on it.

It was a recorded run. A recorded run may illustrate and may not carry a claim, so a figure quoted at
claim strength in a printed table needed a harness behind it.

## Setup

Two arms, both with the package's full source in context, differing only in the instruction:

    full_context   the task, and the subsystem's source
    full_exhort    the same, plus an engineering standard requiring reuse of existing helpers
                   and a written justification for any duplication

The exhortation names no helper. That is the point: it tests willingness while holding visibility
fixed, which is the only way to separate the two. The scorer is the committed deterministic one from
`probe_fullcontext_fragmentation.py`, which greps the produced module for literal calls to the two
canonical helpers.

Twenty trials per arm per family, per the sample-size rule in Appendix C.

## Result — the lift is zero, on both families

| Family | full_context | full_exhort | lift |
|---|---|---|---|
| `claude-haiku-4-5-20251001` | 20/20 | 20/20 | **+0.00** |
| `gpt-5.4-2026-03-05` | 20/20 | 20/20 | **+0.00** |

Both arms reused both canonical helpers in every trial. The original figure reproduces exactly, on a
second vendor, with every prompt and response committed.

## What it means, and what it does not

**The instruction had no room to work, and that is the finding.** An agent that can see the helper
uses it, with or without being told to. The ceiling was already reached by visibility alone, so the
exhortation could not move the number in either direction.

**It is a bounded result, and the boundary is where the book's argument lives.** This says nothing
about the case the method exists for, in which the helper is *not* visible. `no-chokepoint.md`
measures that regime and finds reinvention in every trial. The pair together is the argument:
surfacing moves reuse, and instruction does not move what surfacing has already achieved.

**A ceiling effect cannot rule out a small negative.** Twenty of twenty in both arms means the design
has no headroom to detect an instruction making things slightly worse either. A weaker model, or a
harder task, would be the way to look for that, and neither was run.

**The partial-fit case is different and is not retired.** `reframe-D-coherence-price.md` found that
where a helper only partly fits, pricing the divergence in the instructions did move reuse, four in
ten to six in ten. Under the separation rule that is 20 points at n=10 and reported as no separation
at this sample, but it is a different regime from this one and should not be folded into it.

## Reproduce

    export SSL_CERT_FILE=$(python3 -c "import certifi;print(certifi.where())")
    python3 experiments/harness/dispatch.py --probe probe_fullcontext_fragmentation.py \
        --condition full_context --condition full_exhort --trials 20 \
        --model claude-haiku-4-5-20251001 \
        --out experiments/data/runs/exhortation/<date>-haiku

Re-score committed responses without spending tokens by pointing the scorer at the run directory;
every trial commits its raw response and the extracted module.

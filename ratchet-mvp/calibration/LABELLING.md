# Labelling pairs: the rubric

`coherence-ratchet calibrate sample` writes a JSONL file of function pairs with `"label": null`. A
person sets each one to `same`, `different`, or `unsure`. That judgement is the whole point: the tool
samples and the tool reports, and it does not decide what counts as the same idea, because deciding
that is architectural judgement and this method does not automate it.

## The corpus, and how to label it

`pairs.jsonl` holds 225 pairs sampled from the four control libraries the book characterises, 75 per
library at seed 7, stratified across the whole similarity range and weighted towards the bands either
side of the shipped 0.45 threshold, which is where a threshold decision is actually made.
`provenance.json` pins the commit of each library the pairs were drawn from, so the corpus can be
re-derived rather than trusted.

Each pair carries both functions' source, file, and line, because the question below is not
answerable from two dotted names.

```sh
python3 calibration/build_labeller.py     # writes calibration/label.html, corpus embedded
open calibration/label.html               # label with s / d / u; progress survives a closed tab
# export, save the download as calibration/pairs-labelled.jsonl, then:
coherence-ratchet calibrate score calibration/pairs-labelled.jsonl
calibration/replicate.sh --with-corpus    # re-derive the corpus and re-score the labels
```

The page is a single offline file with the corpus embedded; it makes no network requests and stores
progress in the browser only. It is regenerated from `pairs.jsonl` and is not committed.

Two labellers are better than one, and the disagreement rate is worth reporting when there are two.
With one labeller, say so where the figures are published: a single-labeller ground truth is a real
limit, and the book's own evidence rules require it to be named rather than implied away.

## The question to ask

Not *are these functions similar?* — every pair in the sample is similar to some degree, which is why
they were sampled. The question is:

> **If one of these needed a behaviour change, would the other need the same change?**

That question is answerable, and it is the one the method cares about. Two functions that must change
together are one concept implemented twice, whatever they look like. Two functions that merely
resemble each other are two concepts, and consolidating them would couple things that have no reason
to move together.

- **`same`** — one concept, implemented more than once. A change to the rule behind one is a change
  to the rule behind the other, and a reader who fixed only one would have left a bug.
- **`different`** — two concepts that happen to share a shape. A change to one has no bearing on the
  other.
- **`unsure`** — genuinely unclear, or it depends on information the code does not carry.

## `unsure` is a recorded outcome, not a failure to decide

Forcing an unclear pair into a binary is how a ground truth stops being one. `unsure` pairs are
excluded from the precision and recall figures and counted separately in the report, so a corpus that
was hard to label says so out loud instead of quietly inflating whichever class the labeller leaned
towards. A high `unsure` count is information about the codebase, and it is worth reporting.

## The hard cases, and how to call them

**Protocol-mandated similarity.** Two serialisers, two `__eq__`-style comparisons, two adapters
implementing the same interface. These often look near-identical because a protocol says they must.
Ask the change question: if the protocol changed, would both change? Usually yes — but if each is
bound to a *different* external contract, they are `different`, because they move on separate
schedules.

**Deliberate per-version copies.** A v1 and a v2 handler kept apart on purpose while consumers
migrate. Label `different`. The divergence is a decision somebody made, and the point of the
catalogue is that a sanctioned duplicate is not drift. If you find several of these, that is a signal
the catalogue needs entries, not that the threshold needs moving.

**Thin wrappers.** A function whose whole body delegates to another, with a rename or a default. The
wrapper and its target are not two implementations of one concept; they are one implementation and an
alias. Label `different`, and note that the shipped detector's twelve-token floor already drops most
of them.

**Same shape, different domain.** Two retry loops, one for a payment gateway and one for a log
shipper, with different backoff and different idempotency assumptions. If the retry policy is
genuinely one decision the organisation wants to hold, `same`. If the two have separate operational
reasons to differ, `different`. This is the pair most worth a second labeller.

**Generated code.** Exclude it before sampling rather than labelling it. It is not a design decision
and it will dominate any corpus it appears in.

## Two labellers where possible

Where two people label the same file independently, the report can carry an agreement figure and the
number stops resting on one person's reading. Where only one person labels, say so in the write-up.
A single-labeller ground truth is still worth having and it is not the same artefact as an agreed
one, and the difference belongs in print rather than in a footnote.

## What happens to the labels

`coherence-ratchet calibrate score <file>` reports precision, recall and F1 at every candidate
threshold, with Wilson intervals and the raw counts behind each row. It names the highest-F1
threshold and the most conservative one reaching precision 0.90, and then it stops. It writes nothing
and recommends nothing, because precision and recall trade against each other and the trade is a
judgement about a codebase and the review attention available for it.

It also refuses to report below 100 labelled pairs or 20 positives. A number too unstable to act on
is worse than an absent one, because it looks like evidence.

Record the threshold you choose, and why, in the region's decision record, the way a ceiling is
recorded. A threshold nobody signed is the same problem as a candidate nobody ratified.

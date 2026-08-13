# The reader registry

The book's longitudinal evidence has a hole it names in Chapter 2: every decay curve comes from
human-maintained code, because codebases with years of dense agent authorship *and* enough history to
plot a curve do not exist yet. That treatment arm cannot be bought or hurried. It can only be
recorded, by teams who start measuring before their systems are old enough to show it.

This directory is where those readings are collected. A team that runs the Chapter 2 fieldwork on
their own subsystem can submit the structural readings, anonymised, with one covariate the public
corpus lacks: what share of the code arrived agent-authored.

Nothing here is required to use the method, and nothing here is a condition of anything. It exists
because the measurement that would settle the book's open question is one nobody can take alone.

## What a submission contains

Counts and shapes only. No source, no identifiers, no paths, no literals.

```
coherence-ratchet history <subsystem> --repo . --samples 24 --json reading.json
```

That output, plus the four fields in `submission.schema.json` a person supplies: an opaque project
key the submitter chooses and keeps, the language, a coarse size band, and the agent-authorship
share with the method used to estimate it. The analyser version and the interpreter travel with the
reading already, which is what makes two submissions comparable.

## What is deliberately not collected

No repository name, owner, host, or URL. No file or module names, so a reading cannot be matched back
to a codebase by its structure. No commit hashes, since a hash identifies a public repository exactly.
No dates finer than the month. No headcount, team names, or anything about people.

The anonymisation is the submitter's to verify, not this project's to promise, so
`anonymise.py` runs locally, strips the fields above from a `history` dump, and prints what it
removed. A submission that has not been through it should not be sent.

## Agent-authorship share, and why it is coarse

The one covariate worth having is also the hardest to measure honestly. Commit trailers, bot
accounts, and signed agent commits undercount, because a human pasting agent output leaves no trace,
and they overcount where a person heavily rewrote what an agent drafted. So the field is a band,
not a percentage: `none`, `some`, `about half`, `most`, `nearly all`, with a free-text note on how
it was estimated. A precise number here would be false precision, and the analysis that eventually
uses this corpus should be able to say what the bands meant.

## The standing conflict of interest

This registry is proposed by the author of a book that would benefit from the corpus supporting it.
Two things guard against that. Submissions are published as received, including ones that cut against
the book's argument, and the analysis script ships with the corpus so a reader can run their own.
A registry that only published confirming readings would be worth less than no registry.

## Status

**Not yet open.** The schema and the anonymiser are here so that the design can be criticised before
anything is collected, which is the right order. Opening it needs a submission address and a public
home for the corpus, both of which are the author's to set up and neither of which exists yet.

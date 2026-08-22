# Replication — the consolidation judge on the eight `requests` clusters

**Date:** 13 August 2026. **Probe:** `probe_gate_judge.py`. **Fixture:** `_fixtures/gatejudge/`.
**Runs:** `experiments/data/runs/gatejudge/2026-08-13-{haiku-4-5,gpt-5.4}/`.
**Models:** `claude-haiku-4-5-20251001` and `gpt-5.4-2026-03-05`, 8 clusters × 5 trials × 2 families,
80 calls, temperature 1.0. Every response, a deterministic scorer's output and a pinning manifest are
committed.

Pre-registered before dispatch in `EXPERIMENT-INDEX.md`: mean trial agreement 0.97, C3 answered
SANCTIONED 5/5 against a CONSOLIDATE ground truth, and no CONSOLIDATE verdict on any cluster.

## Result

| | pre-registered | haiku-4-5 | gpt-5.4 |
|---|---|---|---|
| Mean majority fraction | 0.97 | **0.97** | **0.97** |
| C3 (hash helpers) | SANCTIONED 5/5 | CONSOLIDATE 5/5 | CONSOLIDATE 4/5 |
| CONSOLIDATE verdicts, all clusters | 0 | 26 | 4 |
| Unanimous errors against ground truth | C3, C6 | **C1, C4, C8** | **C6** |

**The consistency figure reproduced exactly, on both families. The specific error did not.** Both
current models answer C3 correctly and confidently: the four `*_utf8` hash helpers differ only by the
digest primitive, and both say so.

## What replaced it, and why it is the same finding

The claim the book draws from this experiment is that consistency is not correctness: a judge can agree
with itself almost perfectly and be confidently, unanimously wrong. That reproduced. It moved cluster.

`claude-haiku-4-5-20251001` returns CONSOLIDATE on **C1**, five trials of five, every one at high
confidence. C1 is `get`, `patch`, `post` and `put`: the public HTTP verb API of `requests`. Its stated
reason on trial 00, quoted in full:

> All functions follow an identical pattern of delegating to a shared `request()` function with only
> the HTTP method and parameter signatures varying, making them candidates for a factory function or
> decorator-based approach.

**Correction, 22 August 2026.** An earlier version of this file printed that quotation with its final
clause replaced by "ideal candidates for consolidation", a wording that appears in no committed
response: it spliced the opening of trial 00 onto a truncated tail borrowed from trial 01, and the
truncation removed the clause that carries the model's actual proposal. The full set matters, because
all five trials name a caller-preserving mechanism: "a factory function or decorator-based approach"
(trials 00 and 03), "consolidation into a factory function or decorator pattern" (01), "consolidation
via a factory function or decorator pattern" (02), and "a factory pattern or a single parameterized
implementation" (04). A factory that generates `get`, `post`, `put` and `patch` preserves all four
names and breaks no caller.

So the reading this file previously drew from C1 does not hold. It said acting on the verdict would
consolidate the public interface of one of the most depended-upon libraries in the language; the model
proposed something that would not. What C1 does establish is narrower and still useful: the verdict
token `CONSOLIDATE` is not actionable on its own, because the prompt asked only whether a group
"should be consolidated into one implementation" and never asked what should become of the public
entry points, so the token conflates a change of implementation with a change of interface. An
autonomous gate keyed on the token would act on a decision the model never made. The same model
returns a verdict against the label on C4 and C8; `gpt-5.4-2026-03-05` does so on C6, and answers C1
`SANCTIONED` five times out of five, reasoning that the wrappers are "intentionally separate
convenience methods at different API levels".

So the mechanism is unchanged and the example has moved rather than strengthened. The original judge
was confidently wrong by refusing to consolidate a genuine duplicate. This one is confidently
committed to a verdict whose remedy it did not state, on a cluster where the other family is equally
confident of the opposite. Self-agreement of 0.97 held across both families while the cluster they
were unanimous about changed and their answers on C1 contradicted each other, which is the finding:
consistency measures the model's stability, not its correctness, and no amount of it tells a reader
which family to believe.

## Honest limits, and what this run cannot do

**It cannot refute the original.** The original prompt was never committed. The record describes the
framing (a forced `CONSOLIDATE`/`SANCTIONED`/`UNSURE` schema, objective classification, five trials)
and the prompt here is reconstructed from that description. A different stimulus on a different model
tier is a new experiment, so the 2026-08-12 figures are not disproved by these. They are simply no
longer the best evidence available for the claim they support.

**The clusters and ground truth are the originals.** `semantic-gate-on-requests.md` enumerates all
eight clusters, their members and their hand-assigned labels, which is what makes this a replication of
the design rather than an invention.

**The library moved.** The original run's `requests` revision was not recorded. The committed snippets
come from 2.34.2, so this tests the same clusters and not byte-identical inputs. C3's helpers now carry
`usedforsecurity=False` and type annotations the original may not have shown.

**A fixture defect was found and corrected mid-run.** The first extraction of `to_key_val_list` took an
`@overload` stub rather than the implementation, and four of five trials correctly answered UNSURE,
saying the second function was truncated. The fixture was corrected and both families were re-run from
scratch against the corrected input. The judge caught the defect before the scorer did.

**One model family, one tier each.** Neither family was run at a second tier, so the difference between
haiku's 26 CONSOLIDATE verdicts and gpt's 4 is not attributable to anything this run measured.

## Verdict

The 0.97 consistency figure is reproduced and provenanced, on two dated model snapshots, with every
response committed. The C3 instance is superseded: it is recorded in Appendix C.9 with both figures and
this date, and the manuscript now carries the C1 instance, which is provenanced and demonstrates the
same mechanism more sharply.

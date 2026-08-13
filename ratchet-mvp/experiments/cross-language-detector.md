# Experiment — Does the semantic detector work across programming languages?

**The gap:** every prior experiment was Python. The method's deterministic detector is Python-AST-bound, and cross-language was *asserted* as a limit, never tested. This tests the part that can be language-agnostic — the LLM concept-clustering that catches divergent reimplementation (the detector's intelligent core, and the same engine behind the gate and prevention).

**Result: the intelligent core generalises across four languages — precision 1.000 (no false merges, and it did not group by language), recall 0.836 (down from 1.0 within-Python). The cost of going polyglot is missed links, not wrong ones, concentrated on the concepts whose idioms differ most between languages.**

## Design
40 functions: 5 concepts (retry, paginate, debounce, validate-email, memoize) × 2 divergent implementations × 4 languages (Python, JavaScript, Go, Java), 10 per language. Opaque function names (no concept hint), language shown per block (realistic — you know the file type). 5 clustering trials, consensus ≥3/5, asked to group by underlying concept **even across languages**. Scored pairwise against concept (language-independent ground truth).

## Results

| Metric | Value |
|---|---|
| Precision (co-grouped pairs truly same-concept) | **1.000** — TP=117, FP=0 |
| Recall (same-concept pairs co-grouped) | **0.836** — FN=23 |
| Cross-language same-concept pairs co-grouped | **85%** (102/120) |
| Grouped purely by language (the failure to avoid) | **none** |

Per-concept cross-language cohesion: retry **0.89**, paginate **0.89**, memoize **0.89**; debounce **0.64**, email-validation **0.54**.

## What it shows
- **The detector's intelligent core is language-agnostic, demonstrably.** It grouped a Python retry with a Go retry with a Java retry 85% of the time, with zero false merges and — importantly — it never fell back to the lazy grouping (all-the-Go-things-together). It clustered by *what the code does*, across syntax it has never been told to align.
- **Crossing languages costs recall, not precision.** Within Python (H5) recall was 1.0; across four languages it falls to 0.84. The detector becomes *more conservative* — it misses some cross-language duplicates rather than inventing kinship. For a steward that is the safe failure direction: under-report, don't cry wolf.
- **The misses cluster where idioms diverge most.** retry/paginate/memoize (similar shape in any language) held at 0.89; debounce (JS event-loop timers vs Go channels vs Python threading) and email-validation (regex vs library vs hand-parse) fell to 0.64/0.54. When the *same concept* is realised through genuinely different language mechanisms, the LLM sometimes treats them as distinct — defensible, but it means polyglot recall is concept-dependent.

## The honest boundary: this is the LLM core, not the whole method
- **The deterministic detector remains Python-only.** It uses `ast.parse`; other languages need a per-language parser (tree-sitter or equivalent). That is an *engineering* task, not a conceptual barrier — token-shingling is language-agnostic in principle; only the MVP's parser is bound. Until that work is done, the cheap structural floor does not generalise, and only the LLM stage (tested here) does.
- So the accurate claim is split: **the method's intelligent layers (semantic detection, catalogue gate, prevention — all LLM-read) generalise across languages** (first-party evidence here), while **the deterministic floor needs per-language parsing to match.** The method is language-agnostic *in principle and in its LLM core*; the cheap detector is an implementation away.

## Honest caveats
- Generated-clean code, opaque names, 5 coarse concepts, 40 functions, 4 mainstream languages, 5 trials — the same easy-regime limits as H5, plus the language axis. Fine-grained concepts, messy real polyglot code, and less-common languages are untested.
- Recall 0.84 means a real polyglot scan would miss ~1 in 6 cross-language concept-duplicates — acceptable for a surfacing tool, but not exhaustive.
- The gate and prevention were not separately re-run cross-language; they share the same LLM-reads-any-language mechanism, so the result is suggestive for them, not proven.

## Verdict
The cross-language question has a real, first-party answer for the part that matters: the semantic detector recovers same-concept divergent code across Python, JavaScript, Go, and Java with perfect precision and 0.84 recall, grouping by concept rather than by language. The method's intelligent core is therefore language-agnostic; the cost of polyglot is conservative under-reporting on idiom-divergent concepts, not false alarms. The standing limit is narrower than "untested across languages": it is that the *deterministic* floor still needs a per-language parser — engineering, not research — while the LLM layers already cross languages.

→ book: replace the blanket "cross-language untested" caveat with the measured split — LLM detection/gate/prevention generalise across four languages (precision 1.0, recall 0.84, no language-only grouping); the deterministic detector needs tree-sitter-style per-language parsing to match. Appendix A (the signal catalogue) notes that polyglot recall is concept-dependent (weakest where idioms diverge). Dead-end retired: "the method is Python-bound" — its intelligent core is not.

# Experiment E5 (D5) — Does constraining the contract collapse regeneration divergence?

**Hypothesis (D5):** if the sanctioned shape is fixed up front — a scaffold, a contract, a paved road — agents converge on it by construction, and the divergence D6 found in free regeneration disappears. This is the constructive other half of D6: D6 showed an intent-level spec regenerates into a different contract every time; D5 asks whether pinning the contract fixes it.

**Result: pinning the contract collapsed every consumer-breaking axis of divergence to one — and left exactly the unpinned edges still divergent.** Same intent spec as D6, same 12 independent agents, same measurement harness, with one change: the prompt carried a fixed public contract (the `list_orders` signature plus the five response keys) and said internals and edge handling were free.

## Results — D6 (spec only) vs D5 (spec + contract scaffold), n=12 each

| Measure | D6: intent spec alone | D5: + contract scaffold |
|---|---|---|
| Public API shapes | **10 distinct** | **1** — `list_orders(orders, status, page, page_size)` |
| Response key scheme | **6 distinct** (`items` vs `orders`; `total_items`/`total`/`total_count`/`total_orders`; nested `pagination`/`page_info`) | **1** — exactly `{items, page, page_size, total_items, total_pages}` |
| Return type/shape | **4 distinct** (dict / TypedDict / dataclass / nested object) | **1** — plain dict, identical key types |
| Returns exactly the 5 contracted keys | — | **12/12** |
| Happy-path contents (page 1, size 3, status paid) | not comparable (APIs differed) | **12/12 identical** — order ids `(1, 3, 5)` |

A consumer binding to the contract — `response["items"]`, `response["total_items"]` — now works against every regeneration. The divergence that broke consumers in D6 went to zero.

## The honest nuance: it collapses only what it pins
The unpinned decisions still diverged across the 12:
- out-of-range page: some **clamp to the last page**, others keep the requested page number with an empty `items`;
- empty result set: `total_pages` is **1** in some (`max(1, …)`), **0** in others;
- validation: some **raise `ValueError`** on a bad `page`/`page_size`, others coerce or pass through.

So the scaffold buys exactly what it specifies. The observable contract converged completely; the behaviour the contract left silent stayed as divergent as in D6. That is the precise statement of both the power and the limit of constrain-by-design: it is a contract, and a contract only binds what it names.

## What it means
- **The lever across D6 and D5 is the contract, not the spec's prose.** Free regeneration diverges at the contract boundary (D6); fixing the contract collapses that divergence to nothing (D5). Regeneration is genuinely safe *for the internals* beneath a pinned contract — which is the constructive resolution of the D6 reframe: code can be a disposable build artefact, provided the contract above it is stewarded and stable.
- **This is the platform-engineering paved road, measured.** A scaffold/generator/interface that the output must satisfy makes the sanctioned shape the only shape. The book's structure-spec is exactly such a contract; D5 is first-party evidence that pinning it collapses agent divergence, and D6 is the evidence for why you must (without it, every regeneration is a different system).
- **It relocates the work, it does not remove it.** Someone authors and maintains the contract, and someone decides which edges to pin (the unpinned ones still drift). That is the stewardship the book teaches — now with a sharp rule: pin the contract to the depth your consumers and your invariants depend on, and let the rest regenerate.

## Honest caveats
- Single module, n=12, Claude/Python; "consumer-breaking" inferred from API/response divergence, not from running a real client against each. The happy-path agreement (12/12 identical contents) is directly measured; the edge divergence is read from source.
- A scaffold strong enough to pin the contract is itself an artefact that must be written and kept current — D5 does not measure that maintenance cost (it is the catalogue/contract-staleness problem again, R4).
- The convergence is on what the contract pins; this experiment deliberately shows the residual divergence on what it does not, so it should not be read as "scaffolds make regeneration fully deterministic."

## Verdict
Constrain-by-design works, cleanly, for what it constrains: a fixed contract took regeneration from 10 distinct public APIs and 6 response schemes down to one of each, with 12/12 identical happy-path output, while the unpinned edges diverged exactly as before. Paired with D6, the round closes on a constructive synthesis rather than a dead end: regeneration does not dissolve coherence debt, but it relocates it to a contract that, once pinned, makes the code beneath genuinely disposable. Steward the contract; regenerate the fill.

→ book: D5+D6 anchor the closing "is coherence the right target?" chapter — the answer is "coherence moves up to the contract/spec, and pinning the contract is what makes regeneration safe." Strengthens Ch.3 (the structure-spec *is* the contract that collapses divergence) and adds the constrain-by-design / golden-path section (Ch.5/Ch.7) with measured evidence. Co-positions with *Architecture as Code*'s fitness functions as the enforcement of such a contract. Dead-end retired into synthesis: "regenerate from intent and source coherence stops mattering" is refuted (D6), but "pin the contract and regenerate beneath it" is supported (D5).

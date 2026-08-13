# Experiment E6a (D6) — Does regenerating from a spec dissolve coherence debt?

**The reframe under test (D6):** maybe structural coherence of *source* is the wrong target once AI writes the code. Keep the *spec* coherent, regenerate the module on demand, and treat the code as a disposable build artefact. If regenerations from one fixed spec converge, coherence debt in the code stops mattering — you never maintain code, you maintain the spec.

**Result: regeneration converges only to the degree the spec already pins the observable contract — so the reframe relocates the coherence problem to the spec, it does not dissolve it.** Two regeneration runs, 12 independent agents each, same module regenerated from one spec, then measured for cross-generation agreement.

## Run 1 — a formula-level spec (n=12)
The spec gave the computation as explicit arithmetic (`subtotal = sum(price*qty)`; `discounted = subtotal*(1-discount_rate)`; `total = discounted*(1+tax_rate)`).

| Measure | Result |
|---|---|
| Public API signature | **12/12 identical** — `compute_total(items, discount_rate, tax_rate)` |
| Pinned behaviour (5 unambiguous cases) | **12/12 all correct** |
| Three deliberately *unspecified* edges (rounding, negative qty, fractional cents) | **1 distinct outcome each** — every regeneration returned the same raw float |
| Internal divergence | none material — 0/12 used `Decimal` or `round`; LOC 16–23 |

The "silent" edges weren't actually open: a formula determines the float arithmetic completely, so even the unspecified cases fell out identically. A formula-level spec is code written in prose, and it regenerates to near-identical code.

## Run 2 — an intent-level spec (n=12)
The second spec described the feature the way specs are actually written: "take a list of orders, filter by status, return a paginated view with the page of orders plus enough metadata to render pagination controls." It pinned the *intent*, not the contract.

| Measure | Result |
|---|---|
| Entry signature | converged — 12/12 `(orders, status, page, page_size)` |
| Public API surface | **10 distinct shapes of 12** — function-only vs function + reusable `filter_orders`/`paginate` helpers; result modelled as a plain dict, a `TypedDict`, a frozen `dataclass`, a `PageResult`, or an `OrderPage` nesting a separate `PageInfo`; one regeneration added an `InvalidPaginationError` class, others did not |
| Return type | **4 distinct** (dict / TypedDict / dataclass / nested-object) |
| Response structure — the field names callers depend on | **6 distinct key schemes**: the page list is `items` in some and `orders` in others; the match count is `total_items` vs `total` vs `total_orders` vs `total_count`; two nest a `pagination`/`page_info` sub-object the others flatten |
| Out-of-range behaviour | diverged — one *raises* on a bad page, others clamp or return an empty page |

A consumer written against one regeneration breaks against almost any other: `response["items"]` versus `response["orders"]`, `response["total_items"]` versus `response["total_count"]`, attribute access on a dataclass versus key access on a dict. Every regeneration is a *different system at its contract boundary*.

## What it means
- **Regeneration converges in proportion to how much the spec pins the observable contract.** At one extreme (a formula) the spec is code-in-prose and regeneration is near-deterministic — but then the spec carries the entire coherence burden, and writing/maintaining it coherently is the same stewardship task moved from Python into spec-language. At the other extreme (intent) regeneration produces a fresh, incompatible contract every time.
- **"Code as a disposable build artefact" holds only *beneath a pinned contract*.** Internals can regenerate freely if the public interface and observable behaviour are fixed; it is the contract that must stay stable, because everything downstream binds to it. That is exactly the structure-spec idea the book already carries: pin the shape, leave the fill free. The reframe does not retire stewardship — it moves it up a level, to the contract/spec, and names a new artefact to steward (the contract spec) rather than removing the work.
- **It motivates constrain-by-design (D5).** The way to make regeneration safe is to fix the contract — a scaffold, a generator, an interface the regeneration must satisfy. The convergence half of this experiment is the evidence for that: pin more, diverge less.

## Honest caveats
- **Two single modules, n=12 each, Claude/Python, no consuming code actually run against the regenerations** — divergence was measured by API/structure/return-shape, not by breaking a real client (though the field-name disagreements would break one). A larger, multi-module study with real consumers is the honest sequel.
- **The two specs are endpoints of a spectrum, not a controlled dose-response.** The finding is directional — more contract-pinning, more convergence — not a measured curve. Where on that spectrum a *practical* spec sits (coherent enough to converge, loose enough to be worth writing in prose) is the open question.
- The intent spec's convergence on the entry *signature* (12/12) suggests strong shared priors pull toward common conventions; that may not hold for a less conventional domain.

## Verdict
The bolder reframe — stop caring about source coherence, just regenerate from a coherent spec — does not survive contact with an intent-level spec: regenerations diverge hard at exactly the contract boundary consumers depend on (10/12 distinct APIs, the response field names disagree, dict vs dataclass vs nested object). It is not refuted as *useless* — the formula run shows regeneration converges when the contract is pinned — but it is refuted as an *escape from stewardship*. The problem relocates to keeping a contract spec coherent and stable, which is the same discipline the book teaches, one layer up. The constructive reading, and the bridge to D5: pin the contract and let the internals regenerate beneath it.

→ book: the closing "is coherence even the right target?" chapter gets a measured answer — regeneration moves the coherence problem to the spec/contract layer rather than dissolving it, and is safe for internals only under a pinned contract. Dead-end logged: "regenerate from an intent-level spec and source coherence stops mattering" — refuted, the contract diverges every regeneration. Bridges to D5 (constrain the surface so regeneration converges).

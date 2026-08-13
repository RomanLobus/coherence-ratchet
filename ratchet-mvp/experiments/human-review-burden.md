# Reframe — Does incoherence raise the *human* review burden?

> **RETIRED, 12 August 2026.** Not re-run at higher n: the design cannot ask the question,
> because a language model standing in for a person has neither the bounded working memory nor
> the accountability the claim turns on. Collected in Appendix C.8b, 'the two proxies that could
> not answer the question'. The underlying claims stay OPEN_HYPOTHESIS and need participants.

**The gap E left:** E measured the AI *maintainer* and found incoherence cheap. But the book is for the humans who must **review, approve, and own** AI-written code. This probes the human side — with the honest handicap that the only instrument available is an LLM standing in for the reviewer.

**Result: inconclusive on the human cost — and the reason is itself the finding. The LLM reviewer caught the missed divergent site 10/10 in both full and partial visibility; coherent review was a trivial 10/10. The LLM is too capable to expose the human burden (it masks the effect, exactly as the LLM maintainer did in E). What the probe *does* show is the mechanism by which humans would pay: coherence turns review into a one-step local check; incoherence turns it into a multi-site reconciliation plus inference — and that gap is where bounded human working memory fails, which an LLM does not. The human review-cost of incoherence genuinely requires human subjects to measure; it cannot be settled with the tools used throughout this program.**

## Setup
A PR applies a 10% discount to the order total at one site (`billing.invoice_total`) but the codebase computes the total at a second divergent site (`analytics.revenue_for_order`). The reviewer must approve only if the discount is applied consistently, else name the missed site. Three conditions, n=10:
- **coherent:** one canonical `order_total`; the wrappers delegate (so the PR is genuinely consistent — correct verdict is approve).
- **incoherent-full:** both divergent sites visible.
- **incoherent-partial:** only `billing.py` shown; `analytics.py` listed as existing, body hidden.

## Results

| Condition | Outcome |
|---|---|
| coherent | **10/10 correct approve** — reviewers noted "one canonical site, wrappers delegate, automatically consistent" (a one-step check) |
| incoherent-full | **10/10 caught** the missed `analytics` site; 0 wrongly approved |
| incoherent-partial | **10/10 caught** — inferred the miss from the function's existence and name, despite the hidden body |

## What it means
- **The LLM-reviewer proxy is too capable to measure the human cost.** It reconciled the divergent shapes and even *inferred* a hidden total site from its name — so its catch rate did not drop under incoherence. This is the same masking E hit: the LLM (as maintainer there, reviewer here) outperforms the bounded human the question is actually about. The proxy returns a near-ceiling result that says little about people.
- **But the review *work* differs sharply, and that is the human mechanism.** In the coherent case the reviewers reached the verdict in one move ("there is a single canonical total; done"). In the incoherent case they had to enumerate the divergent shapes, match `qty*price` to `count*cents`, and reason about a site they could not see. Coherence collapses review to a **local check**; incoherence makes it a **global reconciliation**. Humans, unlike the LLM, lose accuracy as that reconciliation grows past working memory — which is exactly the classic case for architectural coherence, now relocated to the AI-authored-code review loop.
- **So the honest position for the book:** coherence's value in AI-assisted delivery is *measured* at the contract/interoperability level (entity-coherence, E's seams) and *argued* on the human side from this local-vs-global review mechanism — but the human review-cost is **not measured here and cannot be with an LLM proxy**. It is the program's clearest genuinely-open frontier, requiring a human study.

## Honest caveats
- LLM-as-reviewer is a weak instrument for a human-cognition question — and here it was *too strong*, masking the effect rather than over-stating it. A real study needs human reviewers, timed, on coherent vs fragmented AI-written code, measuring defect-catch and effort.
- The partial-visibility condition leaked the site via its name (`revenue_for_order`), which the reviewer used — so even the "hidden" case was inferable. A cleaner hidden case would still not fix the proxy-capability problem.
- n=10, Claude/Python, one scenario.

## Verdict
The probe could not demonstrate that incoherence costs the human reviewer — because the LLM proxy is more capable than the human in question and masks the effect, the mirror image of E. Its real contribution is to locate the human cost precisely: coherence makes review a local check, incoherence a global reconciliation, and that is where human (not LLM) working-memory limits bite. This is the honest boundary of the whole program — the **human experience of coherence under AI authorship is the one question the available tools cannot settle**, and it should be named as the central open study rather than papered over with a proxy result.

→ book: Ch.1/Ch.11 and the closing chapter — argue coherence's human value from the *review collapses to a local check* mechanism (and the contract/interop measured cost), while explicitly naming the human review/comprehension study as the open empirical frontier; do not claim the LLM-proxy result as evidence of human cost (it is not). Pairs with E (AI tolerates incoherence) to make the honest combined claim: cheap for the machine, the open question is the human.

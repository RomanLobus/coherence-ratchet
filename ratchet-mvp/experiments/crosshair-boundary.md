# Boundary experiment: CrossHair is not the general comparison engine

**Evidence class:** `REPRODUCIBLE_FIXTURE`  
**Tool:** `crosshair-tool` 0.0.109  
**Fixture:** `crosshair_probe.py`  
**Run date:** 1 August 2026

CrossHair's `diffbehavior` found a concrete difference between the pure integer
half-up and half-even kernels. It reported `amount_thousandths = -15`: the
half-up function returned `-1`, while the half-even function returned `-2`.
The exact input is less important than the result: the symbolic search reached
the rounding tie and refuted equivalence.

The same operation reported no difference between the higher-order retry
functions after more than 500 iterations, although the repository's explicit strategy
fixtures contain two known divergences: a four-attempt operation that succeeds
after three transient failures, and an operation whose `ValueError` must not be
retried. The bounded `coherence-ratchet compare` command finds both because its
strategy constructs fresh stateful callables for each implementation.

Commands:

```sh
crosshair diffbehavior \
  crosshair_probe.round_half_up \
  crosshair_probe.round_half_even \
  --per_condition_timeout=10

crosshair diffbehavior \
  crosshair_probe.retry_original \
  crosshair_probe.retry_mutation \
  --per_condition_timeout=10
```

The second result does not establish equivalence. It establishes a tool
boundary for these fixtures. CrossHair remains useful for suitably pure,
symbolically tractable functions; it is not the book's general verification
engine for arbitrary legacy Python.

---

## Edit notes

- Reproduced the positive and negative cases with CrossHair 0.0.109.
- Recorded the known retry counterexamples and prohibited an equivalence reading of search exhaustion.

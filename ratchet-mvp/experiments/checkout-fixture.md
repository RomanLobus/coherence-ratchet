# Fixture — the checkout-pricing running example, measured for real

**Class:** `REPRODUCIBLE_FIXTURE` (authored). This is not field data and not a mined corpus:
the two states under `playground/_states/{05-checkout-clean,06-checkout-cycle}` are a scripted
illustration of the book's running example, written so that every number the manuscript prints
comes out of the real tool, unedited. The decay is designed in; the measurements are not.

## What was built

A four-module retail pricing seam, `checkout_pricing/`:

- `pricing.py` — rates, rounding, and the canonical `to_minor_units` converter. Fan-in 3:
  every other module depends on it.
- `checkout.py` — builds, settles and cancels orders; carries the campaign schedule and a
  deadline-era copy of the GOLD rate (`Decimal('0.15')`).
- `receipt.py` — renders what the customer sees; re-implements the order total as
  `receipt_total_cents` over `items`/`total_cents` where checkout uses `line_items`/`total`.
- `revenue_report.py` — finance recomputes everything: a third total (`report_total`), plus its
  own converter `as_minor_units` (ROUND_HALF_EVEN where pricing rounds half-up — the half-cent
  divergence the book keeps returning to).

The generator is `playground/checkout_states.py` (same pattern as `billing_states.py`: each state
is the full tree; `materialize()` writes it out). The two states are byte-identical except for
`pricing.promotional_rate`: in `06-checkout-cycle` it reads the campaign schedule out of checkout
through a function-level import — the deadline convenience import that closes the
checkout ↔ pricing cycle without breaking the interpreter.

## The numbers (real tool output, pinned in CI)

`coherence-ratchet measure playground/_states/06-checkout-cycle/checkout_pricing`:

| signal | 05-checkout-clean | 06-checkout-cycle |
|---|---|---|
| modules | 4 | 4 |
| internal edges | 3 | 4 |
| coupling density | 0.75 | 1.0 |
| cycle ratio | 0.0 | 0.5 (2 cyclic / 4 modules) |
| max fan-in ratio | 0.75 (pricing = 3) | 0.75 |
| functions | 31 | 31 |
| redundant functions / clusters | 5 / 2 | 5 / 2 |
| duplication ratio | 0.1613 | 0.1613 |
| connascence (shared literals) | 4 | 4 |

The two redundancy clusters are exactly the canon ones: the three totals
(`checkout.compute_order_total`, `receipt.receipt_total_cents`, `revenue_report.report_total`)
and the two converters (`pricing.to_minor_units`, `revenue_report.as_minor_units`). The four
shared literals are `'0.15'`, `'0.01'`, `'SETTLED'`, `'PENDING'` — each in at least two modules,
and nothing else shared. Because duplication and connascence are identical in both states, a
budget initialised on 05 trips on 06 for one reason only:

```
✗ cycle_ratio: 0.5 (2 cyclic / 4 modules) > ceiling 0.0 (+0.5)
```

`selfmodel derive` on the 06 state surfaces the canon candidates: a `reuse_helper` with concept
`minor` and suggested site `pricing.to_minor_units`, and an `entity_shape` candidate for `order`
whose per-site keys record the fragmented shape (checkout: `line_items`, `total`, `status`;
receipt: `items`, `issued_at`, `reference`; revenue_report: `lines`, `booked_on`, `ref`).

## The scripted history (hyperliminal pair and contagion)

`experiments/scripts/checkout_history_repo.py` builds a throwaway git repository, materialises
the 06 state, and replays ten commits with eighteen module touches: four calibration commits in
which `checkout.py` and `revenue_report.py` change together (no import edge between them — the
report re-implements the totals, so every campaign tweak forces a matching edit), one
pricing+receipt rounding pass, the deadline commit that closes the cycle, and three single-file
tidy-ups. The final tree is asserted byte-identical to the committed 06 state. The history lens
then reads, through `measure --repo`:

```
change history
  hyperliminal pairs ... 1  (diagnostic)
  contagion (mean) ..... 1.8  (diagnostic)
```

The pair is checkout ↔ revenue_report (co-changed 5 of 10 commits, Jaccard 0.71, no static
edge); contagion is 18 touches / 10 commits. The sequence is authored to land on those values —
the script exists so the chapter 5 snapshot has a change-history block that is genuinely printed
by the tool, not so the values carry evidential weight.

## Reproduction

From `ratchet-mvp/`:

```sh
python3 tests/run.py                     # includes tests/test_checkout_fixture.py (50 tests)
coherence-ratchet measure playground/_states/06-checkout-cycle/checkout_pricing
coherence-ratchet init playground/_states/05-checkout-clean/checkout_pricing \
  --budgets coherence/checkout-budgets.json
coherence-ratchet check playground/_states/06-checkout-cycle/checkout_pricing \
  --budgets coherence/checkout-budgets.json     # exits 1: RATCHET TRIPPED on cycle_ratio
python3 experiments/scripts/checkout_history_repo.py   # prints the --repo snapshot above
```

`tests/test_checkout_fixture.py` pins every number in the table, the exact cluster membership,
the four literals, the single-breach behaviour, the selfmodel candidates, and that the committed
state directories match the generator, so drift between the fixture and the manuscript's
transcripts fails CI.

## Limits

- An authored fixture illustrating the book's running example — not evidence that these signal
  values occur in the wild at these rates. The corpus experiments (`requests`, `flask`) carry
  that weight.
- The commit history is scripted, deterministic and openly synthetic; it demonstrates what the
  history lens reports when a hyperliminal pair exists, nothing more.
- Detector thresholds (Jaccard ≥ 0.45, `_significant` literals) are the tool's playground
  calibration; the fixture was written to sit well inside them (in-cluster similarity ≥ 0.67,
  worst off-cluster pair 0.375), not to probe them.
- The states carry no `__init__.py`: the metric engine counts an `__init__.py` as a fifth
  module, and the book's snapshot is a four-module seam. The package still imports as a
  namespace package; nothing in the tests executes it.

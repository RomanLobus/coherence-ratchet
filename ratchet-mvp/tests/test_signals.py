"""Tests for the composite signal portfolio and the multi-signal ratchet.

The point the book leans on: no single metric is enough, so the ratchet watches a portfolio
(duplication + cycles + connascence) while coupling stays diagnostic. These pin that the composite
measures the staged billing states, that the portfolio ratchet trips on decay and holds on
consolidation, and that consolidation raising coupling does NOT trip the ratchet.

Run from ratchet-mvp/:  python -m pytest -q  (or python3 tests/run.py)
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import measure_all
from coherence_ratchet.ratchet import Budget

STATES = os.path.join(ROOT, "playground", "_states")


def _billing(state):
    return os.path.join(STATES, state, "billing")


def test_composite_reports_full_portfolio():
    d = measure_all(_billing("00-baseline")).to_dict()
    for key in ("duplication_ratio", "cycle_ratio", "coupling_density", "connascence_shared"):
        assert key in d, key


def test_portfolio_ratchet_trips_on_decay():
    budget = Budget.from_snapshot(measure_all(_billing("00-baseline")))
    # baseline holds against itself
    assert budget.breaches(measure_all(_billing("00-baseline"))) == []
    # the decayed peak trips, and it trips on MORE than duplication alone
    breaches = budget.breaches(measure_all(_billing("03-loyalty")))
    metrics = {b.metric for b in breaches}
    assert "duplication_ratio" in metrics
    assert "connascence_shared" in metrics  # a second, independent signal fired


def test_consolidation_repays_duplication_but_portfolio_finds_residual():
    # The point of the portfolio: consolidation repays the obvious debt (duplication) and RAISES
    # coupling (healthy, so not ratcheted), while a subtler signal (connascence — the retry count
    # shared by two modules) survives and the ratchet still catches it. A duplication-only gate
    # would go green here; the portfolio does not.
    base = measure_all(_billing("00-baseline")).to_dict()
    fixed = measure_all(_billing("04-consolidated")).to_dict()
    assert fixed["coupling_density"] > base["coupling_density"]   # coupling rose
    budget = Budget.from_snapshot(measure_all(_billing("00-baseline")))
    remaining = {b.metric for b in budget.breaches(measure_all(_billing("04-consolidated")))}
    assert "duplication_ratio" not in remaining   # duplication was actually repaid
    assert "coupling_density" not in remaining     # coupling is diagnostic, never ratcheted
    assert "connascence_shared" in remaining       # the residual the portfolio still catches


def test_function_snapshot_budget_still_works():
    # backward-compat: a duplication-only Snapshot ratchets its subset without the new keys.
    from coherence_ratchet import measure

    budget = Budget.from_snapshot(measure(_billing("00-baseline")))
    assert set(budget.ceilings) <= {
        "redundant_clusters", "redundant_functions", "duplication_ratio",
    }
    assert budget.breaches(measure(_billing("03-loyalty")))  # still trips

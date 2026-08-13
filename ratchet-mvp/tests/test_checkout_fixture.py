"""Pins the checkout-pricing fixture to its published numbers.

The two states under playground/_states/{05-checkout-clean,06-checkout-cycle}
are the manuscript's running example. These tests hold the printed metrics
still: if the fixture drifts, the published transcripts go stale and CI says so.

Run from ratchet-mvp/:  python3 tests/run.py   (or python -m pytest -q)
"""

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "playground"))

import checkout_states as cs
from coherence_ratchet import selfmodel
from coherence_ratchet.ratchet import Budget
from coherence_ratchet.signals import measure_all


def _measure_state(name):
    files = {n: f for (n, _d, f) in cs.STATES}[name]
    d = tempfile.mkdtemp()
    cs.materialize(files, d)
    return measure_all(os.path.join(d, "checkout_pricing"))


def test_clean_state_architecture():
    d = _measure_state("05-checkout-clean").to_dict()
    assert d["n_modules"] == 4
    assert d["n_edges"] == 3
    assert d["coupling_density"] == 0.75
    assert d["cycle_ratio"] == 0.0
    assert d["cyclic_modules"] == 0
    assert d["max_fan_in"] == 3
    assert d["max_fan_in_ratio"] == 0.75


def test_cycle_state_architecture():
    d = _measure_state("06-checkout-cycle").to_dict()
    assert d["n_modules"] == 4
    assert d["n_edges"] == 4
    assert d["coupling_density"] == 1.0
    assert d["cycle_ratio"] == 0.5
    assert d["cyclic_modules"] == 2
    assert d["max_fan_in_ratio"] == 0.75


def test_duplication_identical_in_both_states():
    for name in ("05-checkout-clean", "06-checkout-cycle"):
        comp = _measure_state(name)
        d = comp.to_dict()
        assert d["total_functions"] == 31
        assert d["redundant_functions"] == 5
        assert d["redundant_clusters"] == 2
        assert d["duplication_ratio"] == 0.1613
        assert comp.snapshot.clusters == [
            ["checkout.compute_order_total", "receipt.receipt_total_cents",
             "revenue_report.report_total"],
            ["pricing.to_minor_units", "revenue_report.as_minor_units"],
        ]


def test_connascence_is_the_four_canon_literals():
    for name in ("05-checkout-clean", "06-checkout-cycle"):
        comp = _measure_state(name)
        assert comp.connascence_shared == 4
        values = {row["value"] for row in comp.detail["connascence"]}
        assert values == {"'0.15'", "'0.01'", "'SETTLED'", "'PENDING'"}


def test_ratchet_trips_on_the_cycle_and_only_the_cycle():
    budget = Budget.from_snapshot(_measure_state("05-checkout-clean"))
    assert budget.breaches(_measure_state("05-checkout-clean")) == []
    breaches = budget.breaches(_measure_state("06-checkout-cycle"))
    assert [b.metric for b in breaches] == ["cycle_ratio"]
    assert breaches[0].ceiling == 0.0
    assert breaches[0].observed == 0.5
    assert breaches[0].detail == "2 cyclic / 4 modules"


def test_selfmodel_surfaces_the_canon_candidates():
    files = {n: f for (n, _d, f) in cs.STATES}["06-checkout-cycle"]
    d = tempfile.mkdtemp()
    cs.materialize(files, d)
    model = selfmodel.derive(os.path.join(d, "checkout_pricing"))
    reuse = [c for c in model["candidates"] if c["kind"] == "reuse_helper"]
    entities = [c for c in model["candidates"] if c["kind"] == "entity_shape"]
    assert any(
        c["suggestion"] == {"concept": "minor", "reuse_site": "pricing.to_minor_units"}
        for c in reuse
    )
    assert any(c["suggestion"]["name"] == "order" for c in entities)


def test_committed_states_match_the_generator():
    for name, _desc, files in cs.STATES:
        state_dir = os.path.join(ROOT, "playground", "_states", name)
        for rel, src in files.items():
            path = os.path.join(state_dir, rel)
            with open(path, encoding="utf-8") as f:
                assert f.read() == src, f"{path} has drifted from checkout_states.py"

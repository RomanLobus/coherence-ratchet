"""Tests that pin the MVP's claims: redundancy is detected, the ratchet trips
on decay and holds on consolidation, and the ledger records accepted debt.

Run from ratchet-mvp/:  python -m pytest -q
"""

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "playground"))

import billing_states as bs
from coherence_ratchet import measure
from coherence_ratchet.ratchet import Budget, append_ledger


def _measure_step(label):
    files = {l: f for (l, _n, f) in [(s[0], s[1], s[2]) for s in bs.STEPS]}[label]
    d = tempfile.mkdtemp()
    bs.materialize(files, d)
    return measure(d)


def test_baseline_is_coherent():
    snap = _measure_step("00-baseline")
    assert snap.redundant_clusters == 0
    assert snap.redundant_functions == 0
    assert snap.duplication_ratio == 0.0


def test_divergent_copy_creates_redundancy():
    base = _measure_step("00-baseline")
    after = _measure_step("01-orders")
    assert after.redundant_functions > base.redundant_functions
    assert after.redundant_clusters >= 1


def test_redundancy_rises_monotonically_through_decay():
    seq = [_measure_step(l) for l in ("00-baseline", "01-orders", "02-exports", "03-loyalty")]
    funcs = [s.redundant_functions for s in seq]
    assert funcs == sorted(funcs) and funcs[0] == 0 and funcs[-1] > funcs[0]


def test_consolidation_removes_redundancy():
    decayed = _measure_step("03-loyalty")
    fixed = _measure_step("04-consolidated")
    assert decayed.redundant_clusters > 0
    assert fixed.redundant_clusters == 0


def test_ratchet_trips_on_decay_and_holds_on_consolidation():
    budget = Budget.from_snapshot(_measure_step("00-baseline"))
    assert budget.breaches(_measure_step("00-baseline")) == []
    assert budget.breaches(_measure_step("02-exports"))  # tripped
    assert budget.breaches(_measure_step("04-consolidated")) == []  # held


def test_ledger_records_accepted_debt():
    budget = Budget.from_snapshot(_measure_step("00-baseline"))
    breaches = budget.breaches(_measure_step("01-orders"))
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "ledger.jsonl")
        append_ledger(
            path,
            when="2026-06-25",
            region="billing",
            breaches=breaches,
            owner="billing-steward",
            repayment_trigger="before next orders change",
        )
        with open(path) as f:
            lines = f.read().strip().splitlines()
        assert len(lines) == 1
        import json
        entry = json.loads(lines[0])
        assert entry["region"] == "billing"
        assert entry["owner"] == "billing-steward"
        assert entry["breaches"]

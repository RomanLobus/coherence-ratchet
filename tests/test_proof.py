"""Tests for the behaviour-complete proof — the brake on consolidation.

The headline: the harness catches the three silent behaviour changes the experiments found and a
porous characterisation suite waved through (a rounding-mode flip, a try-count change, and retrying
an exception that should propagate), and it certifies a genuinely faithful consolidation. All offline.

Run from ratchet-mvp/:  python -m pytest -q  (or python3 tests/run.py)
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import proof

FIX = os.path.join(ROOT, "_fixtures", "consolidation")
STRATEGY = os.path.join(FIX, "retry_strategy.py")


def _ref(func):
    return f"{FIX}::variants.{func}"


def test_rounding_flip_is_refuted():
    p = proof.prove(_ref("to_cents_half_up"), _ref("to_cents_half_even"))
    assert p["verdict"] == "REFUTED"
    # the half-cent boundary is where HALF_UP and HALF_EVEN part ways
    assert any("0.005" in c["input"] for c in p["counterexamples"])


def test_retry_divergences_are_refuted():
    p = proof.prove(_ref("retry_orig"), _ref("retry_canon"), strategy=STRATEGY)
    assert p["verdict"] == "REFUTED"
    assert p["counterexamples"]


def test_faithful_consolidation_is_proved():
    p = proof.prove(_ref("retry_orig"), _ref("retry_faithful"), strategy=STRATEGY)
    assert p["verdict"] == "PROVED"
    assert p["counterexamples"] == []


def test_identical_function_proves_against_itself():
    p = proof.prove(_ref("to_cents_half_up"), _ref("to_cents_half_up"))
    assert p["verdict"] == "PROVED"


def test_unknown_signature_is_unproven_without_strategy():
    # retry_orig takes an operation (unknown required type) -> auto-gen can't build it
    p = proof.prove(_ref("retry_orig"), _ref("retry_faithful"))
    assert p["verdict"] == "UNPROVEN"
    assert "strategy" in p["reason"]


def test_exception_type_is_part_of_observed_behaviour():
    def raiser():
        raise ValueError("x")
    assert proof._observe(raiser, (), {}) == ("raise", "ValueError")
    assert proof._observe(lambda: 5, (), {}) == ("return", 5)


def test_seed_library_targets_the_change_points():
    # half-boundary floats and small integers are the seeds that expose rounding and off-by-one
    assert 0.005 in proof._SEEDS[float]
    assert 3 in proof._SEEDS[int] and 4 in proof._SEEDS[int]

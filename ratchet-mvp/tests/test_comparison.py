"""Tests for bounded behavioural comparison.

The harness catches three silent fixture changes: a rounding-mode flip, a try-count change, and
retrying an exception that should propagate. A faithful finite fixture reports only that no
divergence was found in the tested space. All tests run offline.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import comparison

FIX = os.path.join(ROOT, "_fixtures", "consolidation")
STRATEGY = os.path.join(FIX, "retry_strategy.py")


def _ref(func):
    return f"{FIX}::variants.{func}"


def test_rounding_flip_is_refuted():
    packet = comparison.compare(_ref("to_cents_half_up"), _ref("to_cents_half_even"))
    assert packet["verdict"] == "REFUTED"
    assert any("0.005" in item["input"] for item in packet["counterexamples"])


def test_retry_divergences_are_refuted():
    packet = comparison.compare(_ref("retry_orig"), _ref("retry_canon"), strategy=STRATEGY)
    assert packet["verdict"] == "REFUTED"
    assert packet["counterexamples"]


def test_faithful_consolidation_reports_no_divergence_found():
    packet = comparison.compare(_ref("retry_orig"), _ref("retry_faithful"), strategy=STRATEGY)
    assert packet["verdict"] == "NO_DIVERGENCE_FOUND"
    assert packet["counterexamples"] == []


def test_identical_function_retains_bounded_status():
    packet = comparison.compare(_ref("to_cents_half_up"), _ref("to_cents_half_up"))
    assert packet["verdict"] == "NO_DIVERGENCE_FOUND"


def test_unknown_signature_is_unproven_without_strategy():
    packet = comparison.compare(_ref("retry_orig"), _ref("retry_faithful"))
    assert packet["verdict"] == "UNPROVEN"
    assert "strategy" in packet["reason"]


def test_exception_type_is_part_of_observed_behaviour():
    def raiser():
        raise ValueError("x")

    assert comparison._observe(raiser, (), {}) == ("raise", "ValueError")
    assert comparison._observe(lambda: 5, (), {}) == ("return", 5)


def test_seed_library_targets_the_change_points():
    assert 0.005 in comparison._SEEDS[float]
    assert 3 in comparison._SEEDS[int] and 4 in comparison._SEEDS[int]


def _write(root, package, body):
    """Write a one-module package under `root` and return the directory."""
    directory = os.path.join(root, package)
    os.makedirs(directory, exist_ok=True)
    open(os.path.join(directory, "__init__.py"), "w").close()
    with open(os.path.join(directory, "m.py"), "w", encoding="utf-8") as fh:
        fh.write(body)
    return root


def test_same_module_name_under_two_roots_is_not_compared_with_itself():
    """The before/after directory layout is the natural way to compare a consolidation, and Python
    caches imports by module name. Without clearing that cache the second load returned the first
    root's module, both refs resolved to one function object, and maximally divergent code reported
    NO_DIVERGENCE_FOUND — a false clear on the ladder's third rung.
    """
    import tempfile

    base = tempfile.mkdtemp()
    before = _write(os.path.join(base, "before"), "pricing",
                    "def to_minor(x: float) -> int:\n    return int(x * 100 + 0.5)\n")
    after = _write(os.path.join(base, "after"), "pricing",
                   "def to_minor(x: float) -> int:\n    return 0\n")

    packet = comparison.compare(f"{before}::pricing.m.to_minor", f"{after}::pricing.m.to_minor")

    assert packet["verdict"] == "REFUTED", packet
    assert packet["counterexamples"]


def test_a_mutable_argument_is_not_shared_between_the_two_sides():
    """The seed corpus carries lists and dicts. Binding one object to both sides let the original
    mutate the input the replacement was about to receive, so two byte-identical functions that
    append to their argument reported REFUTED.
    """
    import tempfile

    root = _write(tempfile.mkdtemp(), "pkg",
                  "def acc(xs: list) -> int:\n    xs.append(1)\n    return len(xs)\n"
                  "def acc2(xs: list) -> int:\n    xs.append(1)\n    return len(xs)\n")

    packet = comparison.compare(f"{root}::pkg.m.acc", f"{root}::pkg.m.acc2")

    assert packet["verdict"] == "NO_DIVERGENCE_FOUND", packet

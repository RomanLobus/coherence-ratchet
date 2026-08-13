"""Pins the grown checkout fixture, and the dilution case it exists to demonstrate.

`playground/_states/07-checkout-cycle-grown` is the four-module running example at ten modules. It
was built and then never spent: no test referenced it, no chapter used it, and the sync register
listed a chapter-8 block as pending because it needed exactly this fixture.

What ten modules carry that four cannot is a denominator large enough to show the failure the pawl
exists to refuse. Measured against its own smaller twin, the grown tree's cycle ratio **falls** from
0.5 to 0.4 while the number of modules in a cycle **doubles**, from two to four. A ratchet that
watched the ratio alone would read that as an improvement and tighten its ceiling, locking in a
structure that got worse. Until now the book asserted that; here it is, on a committed fixture.
"""

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet.ratchet import init_budget, tighten  # noqa: E402
from coherence_ratchet.signals import measure_all  # noqa: E402

STATES = os.path.join(ROOT, "playground", "_states")
GROWN = os.path.join(STATES, "07-checkout-cycle-grown", "checkout_pricing")
CYCLE = os.path.join(STATES, "06-checkout-cycle", "checkout_pricing")


def _budgets_path():
    return os.path.join(tempfile.mkdtemp(), "budgets.json")


# --- the fixture's readings -------------------------------------------------

def test_grown_fixture_architecture():
    d = measure_all(GROWN).to_dict()

    assert d["n_modules"] == 10
    assert d["n_edges"] == 8
    assert d["coupling_density"] == 0.8
    assert d["cycle_ratio"] == 0.4
    assert d["cyclic_modules"] == 4
    assert d["max_fan_in"] == 3
    assert d["max_fan_in_ratio"] == 0.3


def test_grown_fixture_duplication_and_connascence():
    d = measure_all(GROWN).to_dict()

    assert d["total_functions"] == 34
    assert d["redundant_functions"] == 5
    assert d["redundant_clusters"] == 2
    assert d["duplication_ratio"] == 0.1471
    assert d["connascence_shared"] == 4


def test_the_grown_tree_is_larger_than_the_one_it_grew_from():
    small = measure_all(CYCLE).to_dict()
    grown = measure_all(GROWN).to_dict()

    assert grown["n_modules"] > small["n_modules"]
    assert grown["total_functions"] > small["total_functions"]


# --- the dilution case ------------------------------------------------------

def test_the_ratio_falls_while_the_raw_count_rises():
    """The reading that makes density metrics dangerous under volume inflation."""
    small = measure_all(CYCLE).to_dict()
    grown = measure_all(GROWN).to_dict()

    assert small["cycle_ratio"] == 0.5 and small["cyclic_modules"] == 2
    assert grown["cycle_ratio"] == 0.4 and grown["cyclic_modules"] == 4

    assert grown["cycle_ratio"] < small["cycle_ratio"]      # looks better
    assert grown["cyclic_modules"] > small["cyclic_modules"]  # is worse


def test_the_pawl_declines_to_tighten_against_a_diluted_ratio():
    """A ratchet watching the ratio alone would lock in a structure that got worse."""
    budget = init_budget(CYCLE, _budgets_path(), author="pricing owner", reason="baseline")
    assert budget.ceilings["cycle_ratio"] == 0.5
    assert budget.numerators["cycle_ratio"] == 2

    tightened, declined = tighten(budget, measure_all(GROWN))

    assert tightened.ceilings["cycle_ratio"] == 0.5, "the ceiling must not move"
    reason = declined["cycle_ratio"]
    assert "2 -> 4" in reason
    assert "denominator grew" in reason


def test_the_pawl_still_tightens_when_the_structure_really_improved():
    """The guard must not refuse a real improvement, or it would be a ratchet that never moves."""
    budget = init_budget(CYCLE, _budgets_path(), author="pricing owner", reason="baseline")
    clean = os.path.join(STATES, "05-checkout-clean", "checkout_pricing")

    tightened, declined = tighten(budget, measure_all(clean))

    assert tightened.ceilings["cycle_ratio"] == 0.0
    assert "cycle_ratio" not in declined


# --- two regions in one tree ------------------------------------------------

def test_the_grown_tree_carries_more_than_one_region():
    """Chapter 10 sets two different bars inside one tree; the fixture has to support that."""
    from coherence_ratchet.selfmodel import derive

    modules = {m["module"] for m in derive(GROWN)["observed"]["modules"]}

    # The seam the running example is about, and cells that are plainly not it.
    assert {"pricing", "checkout", "receipt", "revenue_report"} <= modules
    assert len(modules - {"pricing", "checkout", "receipt", "revenue_report"}) >= 4


def test_the_grown_tree_has_a_second_cycle_outside_the_seam():
    """Two regions means two independent problems, not one problem seen twice."""
    from coherence_ratchet.selfmodel import derive

    edges = {m["module"]: set(m.get("depends_on") or [])
             for m in derive(GROWN)["observed"]["modules"]}

    assert "checkout" in edges["pricing"] and "pricing" in edges["checkout"]
    assert "discounts" in edges["campaigns"] and "campaigns" in edges["discounts"]


# --- the layering spec ------------------------------------------------------

def test_the_declared_layering_catches_the_back_edge_with_no_api_key():
    """The deterministic half of the gate runs for free; only the semantic half needs a key."""
    from coherence_ratchet import gate

    report = gate.run(GROWN, layering_path=os.path.join(ROOT, "coherence", "grown-layering.json"))
    violations = report.get("layer_violations") or []

    assert any("pricing" in v and "checkout" in v for v in map(str, violations)), violations


def test_a_layering_violation_can_fail_a_build_and_a_candidate_cannot():
    """The rule the exit codes encode: only something a person declared may turn a build red."""
    from coherence_ratchet import cli

    spec = os.path.join(ROOT, "coherence", "grown-layering.json")
    clean = os.path.join(STATES, "05-checkout-clean", "checkout_pricing")

    # A declared layer order is a human artefact, so violating it is available as a failure.
    assert cli.main(["gate", GROWN, "--layering", spec, "--fail-on", "violation"]) == 1
    # The clean tree still has duplicate clusters nobody ratified. They are surfaced, not failed.
    assert cli.main(["gate", clean, "--layering", spec, "--fail-on", "violation"]) == 3

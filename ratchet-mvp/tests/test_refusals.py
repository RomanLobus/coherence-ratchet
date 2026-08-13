"""The tool must refuse rather than report a clean reading it did not take.

Every test here pins a way the tool could previously report success while having measured nothing.
The first one is the most important test in the package: `measure` against a path that does not
exist returned a complete all-zero snapshot and exit 0, so a renamed directory or a typo in a CI
invocation made `check` pass, and `check --tighten` read the zeros as an improvement and ratcheted
every ceiling to zero. The book tells a reader to put this command in their pipeline. That
instruction is only honest while these tests pass.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import cli  # noqa: E402
from coherence_ratchet.exitcodes import EXIT_REFUSED  # noqa: E402
from coherence_ratchet.paths import SourceTreeError, resolve_root  # noqa: E402
from coherence_ratchet.ratchet import (  # noqa: E402
    Budget, BudgetMalformed, BudgetMissing, tighten,
)

STATES = os.path.join(ROOT, "playground", "_states")
PACKAGE = os.path.join(STATES, "06-checkout-cycle", "checkout_pricing")


class _FakeSnap:
    def __init__(self, d):
        self._d = d

    def to_dict(self):
        return dict(self._d)


def _raises(fn, exc):
    try:
        fn()
    except exc:
        return True
    return False


# --- resolve_root -----------------------------------------------------------

def test_missing_path_is_refused():
    assert _raises(lambda: resolve_root("/definitely/not/a/real/path"), SourceTreeError)


def test_file_instead_of_directory_is_refused():
    fd, path = tempfile.mkstemp(suffix=".py")
    os.close(fd)
    assert _raises(lambda: resolve_root(path), SourceTreeError)


def test_tree_with_no_python_is_refused():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "README.md"), "w") as f:
        f.write("no source here")
    assert _raises(lambda: resolve_root(d), SourceTreeError)


def test_parent_of_the_package_is_refused_with_a_suggestion():
    """The documented footgun: one level up reads zero dependency edges."""
    parent = os.path.join(STATES, "06-checkout-cycle")
    try:
        resolve_root(parent)
    except SourceTreeError as exc:
        assert "checkout_pricing" in str(exc), exc
        return
    raise AssertionError("measuring the directory holding the package was not refused")


def test_the_book_fixtures_are_still_measurable():
    """The guards must not fire on any tree the manuscript prints numbers for."""
    for rel in ("05-checkout-clean/checkout_pricing",
                "06-checkout-cycle/checkout_pricing",
                "07-checkout-cycle-grown/checkout_pricing",
                "03-loyalty/billing"):
        path = os.path.join(STATES, *rel.split("/"))
        if os.path.isdir(path):
            assert resolve_root(path) == path


# --- the CLI turns a refusal into exit 2, not a traceback -------------------

def test_measure_on_a_missing_path_exits_2():
    assert cli.main(["measure", "/definitely/not/a/real/path"]) == EXIT_REFUSED


def test_check_on_a_missing_path_exits_2():
    budgets = os.path.join(tempfile.mkdtemp(), "budgets.json")
    with open(budgets, "w") as f:
        json.dump({"ceilings": {"cycle_ratio": 0.5}}, f)
    assert cli.main(["check", "/definitely/not/a/real/path", "--budgets", budgets]) == EXIT_REFUSED


def test_check_with_a_missing_budgets_file_exits_2():
    missing = os.path.join(tempfile.mkdtemp(), "nope.json")
    assert cli.main(["check", PACKAGE, "--budgets", missing]) == EXIT_REFUSED


def test_check_with_a_malformed_budgets_file_exits_2():
    path = os.path.join(tempfile.mkdtemp(), "budgets.json")
    with open(path, "w") as f:
        f.write("{not json at all")
    assert cli.main(["check", PACKAGE, "--budgets", path]) == EXIT_REFUSED


def test_budgets_file_without_ceilings_is_refused():
    path = os.path.join(tempfile.mkdtemp(), "budgets.json")
    with open(path, "w") as f:
        json.dump({"something_else": 1}, f)
    assert _raises(lambda: Budget.load(path), BudgetMalformed)


def test_absent_budgets_file_names_the_remedy():
    missing = os.path.join(tempfile.mkdtemp(), "nope.json")
    try:
        Budget.load(missing)
    except BudgetMissing as exc:
        assert "init" in str(exc), exc
        return
    raise AssertionError("a missing budgets file did not raise BudgetMissing")


# --- the pawl -------------------------------------------------------------

def test_tighten_declines_against_an_empty_measurement():
    """Belt and braces: even if a zero snapshot arrives by some other route, it is not an
    improvement, and it must not ratchet every ceiling to zero."""
    budget = Budget(ceilings={"cycle_ratio": 0.5, "redundant_clusters": 4})
    tightened, declined = tighten(
        budget, _FakeSnap({"total_functions": 0, "n_modules": 0,
                           "cycle_ratio": 0.0, "redundant_clusters": 0}))

    assert tightened.ceilings == budget.ceilings
    assert set(declined) == {"cycle_ratio", "redundant_clusters"}
    assert all("empty reading" in reason for reason in declined.values())


def test_tighten_is_unaffected_by_a_partial_snapshot():
    """A snapshot that carries neither key is not a whole-tree reading, and the empty-reading guard
    is not its business."""
    budget = Budget(ceilings={"redundant_clusters": 4})
    tightened, declined = tighten(budget, _FakeSnap({"redundant_clusters": 2}))

    assert tightened.ceilings["redundant_clusters"] == 2
    assert declined == {}


# --- the CLI surface the book prints ---------------------------------------

def test_every_subcommand_registers():
    """A swallowed import error used to delete a verb from the CLI silently, with every test still
    passing, so the command table printed in the appendix was unenforced."""
    import argparse

    parser = argparse.ArgumentParser(prog="coherence-ratchet")
    sub = parser.add_subparsers(dest="cmd")
    import importlib

    for name in ("selfmodel", "gate", "comparison", "report", "history", "apidiff"):
        importlib.import_module("coherence_ratchet." + name).register_cli(sub)

    registered = set(sub.choices)
    for verb in ("selfmodel", "gate", "compare", "report", "history", "apidiff"):
        assert verb in registered, f"{verb} did not register"


# --- the exit-code contract holds across the whole surface ------------------

def test_no_subcommand_invents_an_exit_code():
    """Appendix C prints the contract as uniform across every subcommand, so it has to be.

    Only 0, 1, 2, 3 and 4 may be returned. A verb that invented a fifth would make the printed table
    false, and a pipeline encoding "4 is a failure, never a pass" would be encoding a fiction.
    """
    import ast
    import os

    pkg = os.path.join(ROOT, "coherence_ratchet")
    allowed = {0, 1, 2, 3, 4}
    offenders = []
    for name in sorted(os.listdir(pkg)):
        if not name.endswith(".py"):
            continue
        tree = ast.parse(open(os.path.join(pkg, name), encoding="utf-8").read())
        for fn in ast.walk(tree):
            if not (isinstance(fn, ast.FunctionDef) and fn.name.endswith("run_cli")):
                continue
            for node in ast.walk(fn):
                if (isinstance(node, ast.Return) and isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, int)
                        and node.value.value not in allowed):
                    offenders.append(f"{name}:{node.lineno} returns {node.value.value}")
    assert not offenders, offenders


def test_a_close_that_matched_nothing_is_a_usage_error_not_a_crossed_line():
    """Exit 1 is reserved for a ceiling or a ratification. A typo in --region must not look like
    structural worsening."""
    import json

    ledger = os.path.join(tempfile.mkdtemp(), "ledger.jsonl")
    with open(ledger, "w") as f:
        f.write(json.dumps({"region": "billing", "when": "2026-01-01", "status": "accepted"}) + "\n")

    assert cli.main(["close", "no-such-region", "--ledger", ledger,
                     "--by", "someone", "--reason", "test"]) == EXIT_REFUSED

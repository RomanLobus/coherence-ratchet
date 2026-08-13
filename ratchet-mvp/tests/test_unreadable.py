"""A file the parser cannot read must not read as a module that imports nothing.

This pins the defect that made the same pinned commit measure 9 dependency edges or 18 depending
on which Python ran the analyser: two Python-2-era files in an early flask tree raise SyntaxError
on one interpreter and parse on another, and `_edges_for` swallowed the failure and returned an
empty edge set. Silence was the bug; the count is the fix.
"""

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet.archmetrics import measure_arch  # noqa: E402


def _tree(**files):
    d = tempfile.mkdtemp()
    pkg = os.path.join(d, "pkg")
    os.makedirs(pkg)
    for name, body in files.items():
        with open(os.path.join(pkg, name + ".py"), "w", encoding="utf-8") as f:
            f.write(body)
    return pkg


def test_an_unreadable_file_is_counted_not_swallowed():
    root = _tree(
        __init__="",
        good="from pkg import other\n",
        other="VALUE = 1\n",
        broken="except ValueError, e:\n",   # Python 2 syntax; unparseable here
    )
    snap = measure_arch(root).as_dict()
    assert snap["unreadable_modules"] == 1, snap


def test_a_clean_tree_reports_none_unreadable():
    root = _tree(__init__="", a="from pkg import b\n", b="X = 1\n")
    assert measure_arch(root).as_dict()["unreadable_modules"] == 0


def test_the_book_fixtures_are_all_readable():
    """Every tree the manuscript prints a number for must parse completely, or the printed
    number is missing edges it never mentions."""
    states = os.path.join(ROOT, "playground", "_states")
    for rel in ("05-checkout-clean/checkout_pricing", "06-checkout-cycle/checkout_pricing",
                "07-checkout-cycle-grown/checkout_pricing", "03-loyalty/billing"):
        path = os.path.join(states, *rel.split("/"))
        if os.path.isdir(path):
            assert measure_arch(path).as_dict()["unreadable_modules"] == 0, rel

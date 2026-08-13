"""The evidence machinery must obey the rule it enforces elsewhere: a failure is not a clean result.

Both defects here shipped and both produced plausible output, which is what made them dangerous. A
two-arm run whose every trial failed exited 0 with an empty run directory. And the probe's own tally
counted each trial two or three times while silently omitting an arm the probe declares.
"""

import io
import os
import sys
import tempfile
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "experiments", "harness"))

import probe_fullcontext_fragmentation as probe  # noqa: E402

REUSED = "from billing.money import to_cents\nfrom billing.net import retry\n\n\ndef charge(rows):\n    return to_cents(sum(rows))\n"


def _run_dir(**conditions):
    d = tempfile.mkdtemp()
    for cond, n in conditions.items():
        os.makedirs(os.path.join(d, cond))
        for i in range(n):
            base = os.path.join(d, cond, f"trial-{i:02d}")
            # Every trial writes three files. Only one of them is the scored artefact.
            open(base + ".extracted.py", "w").write(REUSED)
            open(base + ".round0.py", "w").write(REUSED)
            open(base + ".raw.json", "w").write("{}")
    return d


def _tally(d):
    buf = io.StringIO()
    with redirect_stdout(buf):
        probe.tally(d)
    return buf.getvalue()


def test_tally_counts_one_row_per_trial_not_per_file():
    """n was three times the trials actually run, because the glob matched every .py a trial wrote."""
    out = _tally(_run_dir(full_context=20))
    line = next(l for l in out.splitlines() if l.startswith("full_context"))
    assert " 20 " in line, line
    assert "60" not in line, line


def test_tally_reports_every_condition_the_probe_declares():
    """An arm added to the probe must not be silently absent from its own results."""
    out = _tally(_run_dir(full_context=5, full_exhort=5))
    assert "full_exhort" in out, out


def test_tally_names_a_condition_it_does_not_recognise():
    out = _tally(_run_dir(full_context=3, invented_arm=3))
    assert "invented_arm" in out
    assert "not declared in CONDITIONS" in out


def test_tally_says_so_when_an_arm_produced_no_code():
    d = _run_dir(full_context=2)
    os.makedirs(os.path.join(d, "full_exhort"))
    out = _tally(d)
    assert "no extracted code" in out, out


def test_every_declared_condition_builds_a_prompt():
    """A condition in CONDITIONS with no branch in build_prompt fails at run time, after the tokens
    have been spent."""
    for cond in probe.CONDITIONS:
        assert probe.build_prompt(cond), cond

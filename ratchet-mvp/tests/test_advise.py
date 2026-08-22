"""The detect half of the loop, and the line between advising and deciding.

These tests pin the property that separates this tool from a detector: a candidate nobody ratified
never fails a build, and the same collision becomes an imperative the moment a named person ratifies
the canonical site. The escalation is the whole design, so it is tested as a pair.

The fixtures are the playground's own copy-and-diverge progression rather than invented code, because
the tool's redundancy clusters there are already pinned by other tests and by the manuscript.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import advise, cli  # noqa: E402
from coherence_ratchet.exitcodes import (  # noqa: E402
    EXIT_ADVISORY, EXIT_CROSSED, EXIT_HELD, EXIT_NOT_MEASURED,
)

STATES = os.path.join(ROOT, "playground", "_states")


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)


def _repo_with_a_copied_helper():
    """02-exports committed, then 03-loyalty's copy of the retry helper staged on top."""
    d = tempfile.mkdtemp()
    shutil.copytree(os.path.join(STATES, "02-exports", "billing"), os.path.join(d, "billing"))
    _git(["init", "-q", "."], d)
    _git(["add", "-A"], d)
    _git(["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"], d)
    shutil.copy(os.path.join(STATES, "03-loyalty", "billing", "loyalty.py"),
                os.path.join(d, "billing", "loyalty.py"))
    _git(["add", "-A"], d)
    return d


def _run(workspace, argv):
    cwd = os.getcwd()
    os.chdir(workspace)
    try:
        return cli.main(argv)
    finally:
        os.chdir(cwd)


def _ratify_the_retry_helper(workspace):
    _run(workspace, ["selfmodel", "derive", "billing", "--model", "coherence/selfmodel.json"])
    with open(os.path.join(workspace, "coherence", "selfmodel.json")) as f:
        model = json.load(f)
    candidate = next(c["id"] for c in model["candidates"]
                     if c["kind"] == "reuse_helper" and "retry" in json.dumps(c).lower())
    _run(workspace, ["selfmodel", "ratify", candidate,
                     "--model", "coherence/selfmodel.json",
                     "--intent", "coherence/intent.json",
                     "--by", "billing owner",
                     "--rationale", "one retry policy for the billing seam",
                     "--scope", "billing"])


# --- the escalation ---------------------------------------------------------

def test_an_unratified_collision_is_surfaced_and_does_not_fail_the_build():
    """A candidate that could fail a build would make this a detector that decides."""
    workspace = _repo_with_a_copied_helper()

    assert _run(workspace, ["advise", "billing", "--staged"]) == EXIT_ADVISORY


def test_the_same_collision_fails_once_a_person_ratifies_the_canonical_site():
    workspace = _repo_with_a_copied_helper()
    _ratify_the_retry_helper(workspace)

    assert _run(workspace, ["advise", "billing", "--staged"]) == EXIT_CROSSED


def test_a_ratified_conflict_quotes_the_authority_it_acts_on():
    workspace = _repo_with_a_copied_helper()
    _ratify_the_retry_helper(workspace)

    findings = _findings(workspace)
    conflict = next(f for f in findings if f["class"] == advise.RATIFIED_CONFLICT)
    instruction = advise.render_instruction(conflict)

    assert "billing owner" in instruction
    assert conflict["ratification"]["reuse_site"] in instruction
    # The out must be stating a reason, not overriding a flag.
    assert "state why" in instruction


def test_a_candidate_finding_says_it_is_not_an_instruction():
    workspace = _repo_with_a_copied_helper()
    finding = next(f for f in _findings(workspace) if f["class"] == advise.CANDIDATE_COLLISION)
    instruction = advise.render_instruction(finding)

    assert "not an instruction" in instruction
    assert "leave the judgement to a person" in instruction


def _findings(workspace):
    model_path = os.path.join(workspace, "coherence", "selfmodel.json")
    intent_path = os.path.join(workspace, "coherence", "intent.json")
    model = json.load(open(model_path)) if os.path.exists(model_path) else {}
    intent = json.load(open(intent_path)) if os.path.exists(intent_path) else {}
    root = os.path.join(workspace, "billing")
    files = {os.path.join(root, "loyalty.py")}
    return advise.analyse(root, files, model, intent)


# --- a ratification is found across the family, not only the nearest match ---

def test_a_ratification_is_found_through_the_redundancy_family():
    """Clustering is transitive: the copy sits above the threshold against one family member and
    below it against the canonical helper the team actually ratified. A pairwise-only check reports
    the one finding that carries authority as an unratified candidate."""
    workspace = _repo_with_a_copied_helper()
    _ratify_the_retry_helper(workspace)

    conflict = next(f for f in _findings(workspace) if f["class"] == advise.RATIFIED_CONFLICT)
    # The ratified site need not be the closest match.
    assert conflict["matched_site"] == conflict["ratification"]["reuse_site"]


# --- nothing to report ------------------------------------------------------

def test_a_change_that_collides_with_nothing_is_held():
    d = tempfile.mkdtemp()
    shutil.copytree(os.path.join(STATES, "00-baseline", "billing"), os.path.join(d, "billing"))
    _git(["init", "-q", "."], d)
    _git(["add", "-A"], d)
    _git(["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base"], d)
    with open(os.path.join(d, "billing", "unrelated.py"), "w") as f:
        f.write("def describe_weather(city, temperature_c, humidity_pct, wind_kph):\n"
                "    summary = f'{city}: {temperature_c}C'\n"
                "    if humidity_pct > 80:\n"
                "        summary += ' humid'\n"
                "    if wind_kph > 30:\n"
                "        summary += ' windy'\n"
                "    return summary\n")
    _git(["add", "-A"], d)

    assert _run(d, ["advise", "billing", "--staged"]) == EXIT_HELD


# --- a change that could not be read is not a clean result ------------------

def test_an_unreadable_change_is_not_measured_rather_than_clean():
    """Reporting 'no findings' when the diff could not be read is the defect this tool names."""
    d = tempfile.mkdtemp()
    shutil.copytree(os.path.join(STATES, "00-baseline", "billing"), os.path.join(d, "billing"))

    assert _run(d, ["advise", "billing", "--staged"]) == EXIT_NOT_MEASURED


def test_no_value_of_fail_on_lets_a_candidate_fail_a_build():
    """The invariant, tested as behaviour rather than as spelling.

    The predecessor asserted `set(action.choices) == {"ratified", "any", "none"}`. It read as a
    guarantee against failing on a candidate and was in fact a lock holding `any` in place, which is
    the one value that did exactly that: `--fail-on any` tested every finding rather than the ratified
    ones, so a candidate-only run exited 1. Driving every advertised choice through a candidate-only
    workspace cannot be satisfied by renaming a flag, which is the point.
    """
    import argparse

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    advise.register_cli(sub)
    action = next(a for a in sub.choices["advise"]._actions if a.dest == "fail_on")

    assert "candidate" not in action.choices
    assert action.default == "ratified"

    for choice in action.choices:
        workspace = _repo_with_a_copied_helper()
        code = _run(workspace, ["advise", "billing", "--staged", "--fail-on", choice])
        assert code != EXIT_CROSSED, f"--fail-on {choice} failed a build on a candidate"

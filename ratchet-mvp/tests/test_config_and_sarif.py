"""Optional settings that cannot move a printed number, and machine-readable findings.

The config file is opt-in and absent by default, which is what keeps a behaviour-changing release
safe for byte-frozen printed output. The SARIF severities carry the same rule the exit codes do: a
candidate is never a violation.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet.advise import (  # noqa: E402
    CANDIDATE_COLLISION, RATIFIED_CONFLICT, to_sarif,
)
from coherence_ratchet.config import ConfigError, is_ignored, load, load_ignore  # noqa: E402


def _raises(fn):
    try:
        fn()
    except ConfigError as exc:
        return str(exc)
    return None


def test_absent_config_yields_no_settings():
    """The default state of every repository, including this project's fixtures."""
    assert load(tempfile.mkdtemp()) == ({}, [])


def test_the_repository_ships_no_config():
    """A config file in the repository would silently change what the published readings print."""
    assert not os.path.exists(os.path.join(ROOT, "coherence", "config.json"))


def test_an_applied_setting_is_reported_not_silent():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "coherence"))
    with open(os.path.join(d, "coherence", "config.json"), "w") as f:
        json.dump({"similarity": 0.6}, f)
    settings, notes = load(d)
    assert settings == {"similarity": 0.6}
    assert notes and "not the shipped default" in notes[0]


def test_an_unknown_key_is_refused():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "coherence"))
    with open(os.path.join(d, "coherence", "config.json"), "w") as f:
        json.dump({"simmilarity": 0.6}, f)
    msg = _raises(lambda: load(d))
    assert msg and "unknown key" in msg


def test_ignore_patterns_match_paths_and_segments():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, ".coherenceignore"), "w") as f:
        f.write("# generated\nvendor/\n*_pb2.py\n")
    pats = load_ignore(d)
    assert is_ignored("vendor/x.py", pats)
    assert is_ignored("a/vendor/y.py", pats)
    assert is_ignored("api_pb2.py", pats)
    assert not is_ignored("app.py", pats)


def _findings():
    return [
        {"class": RATIFIED_CONFLICT, "added": "m.f", "file": "m.py", "line": 5,
         "matched_site": "p.g", "collides_with": ["p.g"],
         "ratification": {"approved_by": "owner", "approved_at": "2026-08-12",
                          "scope": "seam", "reuse_site": "p.g"}},
        {"class": CANDIDATE_COLLISION, "added": "m.h", "file": "m.py", "line": 20,
         "matched_site": None, "collides_with": ["p.k"], "ratification": None},
    ]


def test_sarif_is_wellformed_and_locates_findings():
    doc = to_sarif(_findings(), ".")
    assert doc["version"] == "2.1.0"
    results = doc["runs"][0]["results"]
    assert len(results) == 2
    loc = results[0]["locations"][0]["physicalLocation"]
    assert loc["artifactLocation"]["uri"] == "m.py"
    assert loc["region"]["startLine"] == 5


def test_a_candidate_is_never_a_violation_in_sarif():
    """The exit-code rule in another vocabulary. `warning` would invite a team to treat an
    unratified heuristic as a rule, or to configure it away; it is neither."""
    doc = to_sarif(_findings(), ".")
    by_rule = {r["ruleId"]: r["level"] for r in doc["runs"][0]["results"]}
    assert by_rule[RATIFIED_CONFLICT] == "error"
    assert by_rule[CANDIDATE_COLLISION] == "note"
    levels = {r["id"]: r["defaultConfiguration"]["level"]
              for r in doc["runs"][0]["tool"]["driver"]["rules"]}
    assert levels[CANDIDATE_COLLISION] == "note"
    assert "warning" not in levels.values()

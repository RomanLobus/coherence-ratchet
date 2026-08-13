"""Importing another tool's measurement, and the four things that must be refused.

The fixture is an excerpt of the real committed baseline from `drift` (github.com/mick-gsk/drift),
kept to at most three findings per signal so the counts can be checked by hand. It carries the
producer's own BOM, its own version, and its composite score, so the refusals below are tested
against the shape a reader will actually meet rather than against an invented one.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import cli  # noqa: E402
from coherence_ratchet.exitcodes import EXIT_CROSSED, EXIT_HELD, EXIT_REFUSED  # noqa: E402
from coherence_ratchet.interchange import (  # noqa: E402
    MEASUREMENT_SCHEMA, ImportRefused, load_measurement, read_drift,
)

FIXTURE = os.path.join(ROOT, "_fixtures", "interchange", "drift-baseline-v1.json")


def _raises(fn, exc=ImportRefused):
    try:
        fn()
    except exc as caught:
        return str(caught)
    return None


def _tmp(name, doc):
    path = os.path.join(tempfile.mkdtemp(), name)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(doc, handle)
    return path


def _fixture_doc():
    with open(FIXTURE, encoding="utf-8-sig") as handle:
        return json.load(handle)


# --- reading the producer ---------------------------------------------------

def test_the_committed_drift_fixture_imports():
    m = read_drift(FIXTURE)
    doc = _fixture_doc()
    assert sum(m.counts.values()) == len(doc["findings"])
    assert all(k.startswith("drift.") for k in m.counts), m.counts
    assert m.meta["produced_by"]["tool"] == "drift"
    assert m.meta["produced_by"]["version"] == doc["drift_version"]


def test_imported_counts_are_candidates_never_observations():
    """The tool did not read that code, and the serialised form has to say so."""
    assert read_drift(FIXTURE).as_json()["epistemic"] == "candidate"


def test_the_producer_travels_with_the_counts():
    produced = read_drift(FIXTURE).as_json()["produced_by"]
    for field in ("tool", "version", "producer_schema", "adapter"):
        assert produced.get(field), f"{field} missing from provenance"


# --- the four refusals ------------------------------------------------------

def test_a_score_without_counts_is_refused():
    """The central rule: a composite falls as the denominator grows while the counts hold, so a
    producer offering only a score cannot be ratcheted honestly."""
    path = _tmp("score.json", {"baseline_version": 1, "drift_score": 0.526, "finding_count": 339})
    message = _raises(lambda: read_drift(path))
    assert message and "dilution" in message, message


def test_an_unread_producer_schema_is_refused_by_number():
    path = _tmp("v2.json", {"baseline_version": 2, "findings": []})
    message = _raises(lambda: read_drift(path))
    assert message and "baseline_version=2" in message, message


def test_a_producer_disagreeing_with_itself_is_refused():
    doc = _fixture_doc()
    doc["finding_count"] = doc["finding_count"] + 7
    message = _raises(lambda: read_drift(_tmp("mismatch.json", doc)))
    assert message and "Refusing to choose" in message, message


def test_a_measurement_without_raw_counts_is_refused():
    """The interchange takes raw counts only. A ratio arriving as a bare number has no numerator
    behind it, and the pawl reads numerators."""
    path = _tmp("m.json", {
        "schema": MEASUREMENT_SCHEMA,
        "counts": {"drift.architecture_violation": {"score": 0.4}},
    })
    message = _raises(lambda: load_measurement(path))
    assert message and "raw count" in message, message


# --- the round trip, and the ratchet on top of it ---------------------------

def test_import_then_baseline_then_check_holds_and_trips():
    work = tempfile.mkdtemp()
    measurement = os.path.join(work, "measurement.json")
    budgets = os.path.join(work, "budgets.json")

    assert cli.main(["import", "drift", FIXTURE, "--out", measurement, "--quiet"]) == EXIT_HELD
    assert cli.main(["init", "--from-measurement", measurement, "--budgets", budgets,
                     "--by", "platform owner", "--reason", "baseline from a drift export"]) == EXIT_HELD
    assert cli.main(["check", "--from-measurement", measurement, "--budgets", budgets]) == EXIT_HELD

    worse = json.load(open(measurement, encoding="utf-8"))
    signal = sorted(worse["counts"])[0]
    worse["counts"][signal]["raw"] += 5
    worse_path = os.path.join(work, "worse.json")
    json.dump(worse, open(worse_path, "w", encoding="utf-8"))
    assert cli.main(["check", "--from-measurement", worse_path, "--budgets", budgets]) == EXIT_CROSSED


def test_an_imported_baseline_records_where_the_counts_came_from():
    work = tempfile.mkdtemp()
    measurement = os.path.join(work, "measurement.json")
    budgets = os.path.join(work, "budgets.json")
    cli.main(["import", "drift", FIXTURE, "--out", measurement, "--quiet"])
    cli.main(["init", "--from-measurement", measurement, "--budgets", budgets,
              "--by", "platform owner", "--reason", "baseline from a drift export"])

    provenance = json.load(open(budgets, encoding="utf-8"))["provenance"]
    assert provenance["author"] == "platform owner"
    assert provenance["imported_from"]["tool"] == "drift", provenance


def test_every_producer_signal_is_watched():
    """Dropping the signals this tool does not recognise would baseline a narrower portfolio than
    the reader believes they set."""
    work = tempfile.mkdtemp()
    measurement = os.path.join(work, "measurement.json")
    budgets = os.path.join(work, "budgets.json")
    cli.main(["import", "drift", FIXTURE, "--out", measurement, "--quiet"])
    cli.main(["init", "--from-measurement", measurement, "--budgets", budgets,
              "--by", "platform owner", "--reason", "baseline"])

    imported = set(load_measurement(measurement).counts)
    ceilings = set(json.load(open(budgets, encoding="utf-8"))["ceilings"])
    assert ceilings == imported, imported ^ ceilings


# --- the CLI keeps its contract --------------------------------------------

def test_check_without_a_path_or_a_measurement_is_refused():
    """`path` became optional so `--from-measurement` could stand in for it. Neither one present
    must refuse, not measure the working directory."""
    work = tempfile.mkdtemp()
    budgets = os.path.join(work, "budgets.json")
    json.dump({"ceilings": {"drift.x": 1}}, open(budgets, "w", encoding="utf-8"))
    assert cli.main(["check", "--budgets", budgets]) == EXIT_REFUSED


def test_init_without_a_path_or_a_measurement_is_refused():
    work = tempfile.mkdtemp()
    assert cli.main(["init", "--budgets", os.path.join(work, "b.json"),
                     "--by", "someone", "--reason", "test"]) == EXIT_REFUSED


def test_an_existing_budgets_file_is_not_silently_replaced():
    work = tempfile.mkdtemp()
    measurement = os.path.join(work, "measurement.json")
    budgets = os.path.join(work, "budgets.json")
    cli.main(["import", "drift", FIXTURE, "--out", measurement, "--quiet"])
    args = ["init", "--from-measurement", measurement, "--budgets", budgets,
            "--by", "platform owner", "--reason", "baseline"]
    assert cli.main(args) == EXIT_HELD
    assert cli.main(args) == EXIT_REFUSED

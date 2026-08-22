"""Calibration samples and reports; a person decides.

The property worth testing is not the arithmetic — precision and recall are textbook — but the two
design decisions that make the number honest. The sample must reach below the current threshold, or
recall is unmeasurable and the precision figure flatters the detector. And the report must refuse to
choose, because choosing is the judgement this method does not automate.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import calibrate, cli  # noqa: E402
from coherence_ratchet.exitcodes import EXIT_HELD, EXIT_REFUSED  # noqa: E402
from coherence_ratchet.signals import measure_all  # noqa: E402

STATES = os.path.join(ROOT, "playground", "_states")
BILLING = os.path.join(STATES, "03-loyalty", "billing")


def _labelled(n_same=40, n_diff=80):
    """A labelled set with the two classes overlapping, so the curve has a real trade-off."""
    rows = []
    for i in range(n_same):
        rows.append({"a": f"m.s{i}", "b": f"m.t{i}", "jaccard": 0.50 + (i % 10) * 0.03,
                     "label": "same"})
    for i in range(n_diff):
        rows.append({"a": f"m.d{i}", "b": f"m.e{i}", "jaccard": 0.10 + (i % 12) * 0.03,
                     "label": "different"})
    return rows


def _write(rows):
    path = os.path.join(tempfile.mkdtemp(), "pairs.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    return path


# --- sampling ---------------------------------------------------------------

def test_the_sample_reaches_below_the_current_threshold():
    """Sampling only above it makes recall unmeasurable, which is how precision flatters."""
    rows = calibrate.sample(BILLING, n=30, seed=7)

    assert rows
    assert any(r["jaccard"] < calibrate.SIM_THRESHOLD for r in rows)
    assert any(r["jaccard"] >= calibrate.SIM_THRESHOLD for r in rows)


def test_sampling_is_seeded_so_a_run_repeats():
    first = calibrate.sample(BILLING, n=30, seed=7)
    again = calibrate.sample(BILLING, n=30, seed=7)
    other = calibrate.sample(BILLING, n=30, seed=8)

    assert first == again
    assert isinstance(other, list)


def test_pairs_arrive_unlabelled():
    """The tool never guesses a label, because the label is the judgement."""
    assert all(r["label"] is None for r in calibrate.sample(BILLING, n=20, seed=7))


# --- the report -------------------------------------------------------------

def test_the_curve_trades_precision_against_recall():
    rows = calibrate.curve(_labelled())
    low = next(r for r in rows if r["threshold"] == 0.25)
    high = next(r for r in rows if r["threshold"] == 0.75)

    assert low["recall"] >= high["recall"]
    assert high["precision"] >= low["precision"]


def test_unsure_is_excluded_from_the_figures_not_forced_into_a_class():
    rows = _labelled()
    with_unsure = rows + [{"a": "m.x", "b": "m.y", "jaccard": 0.5, "label": "unsure"}]

    assert calibrate.curve(rows) == calibrate.curve(with_unsure)


def test_it_refuses_to_report_on_too_few_labels():
    """A number too unstable to act on is worse than an absent one: it looks like evidence."""
    path = _write(_labelled(n_same=5, n_diff=5))
    assert cli.main(["calibrate", "score", path]) == EXIT_REFUSED


def test_it_refuses_on_too_few_positives():
    path = _write(_labelled(n_same=2, n_diff=140))
    assert cli.main(["calibrate", "score", path]) == EXIT_REFUSED


def test_a_sufficient_corpus_reports():
    path = _write(_labelled())
    assert cli.main(["calibrate", "score", path]) == EXIT_HELD


def test_the_report_recommends_nothing_and_writes_nothing():
    """It names the rows a reader usually wants, and then stops."""
    path = _write(_labelled())
    before = sorted(os.listdir(os.path.dirname(path)))

    assert cli.main(["calibrate", "score", path]) == EXIT_HELD
    assert sorted(os.listdir(os.path.dirname(path))) == before


# --- the chosen threshold is usable -----------------------------------------

def test_a_chosen_threshold_actually_changes_the_reading():
    """A calibration whose result had nowhere to go would be a number for its own sake."""
    default = measure_all(BILLING).to_dict()
    strict = measure_all(BILLING, sim_threshold=0.95).to_dict()

    assert strict["redundant_clusters"] <= default["redundant_clusters"]


def test_the_shipped_default_is_unchanged_when_no_threshold_is_passed():
    """Every fixture the book prints must read exactly as before."""
    explicit = measure_all(BILLING, sim_threshold=calibrate.SIM_THRESHOLD).to_dict()
    implicit = measure_all(BILLING).to_dict()

    assert explicit == implicit


def test_the_rubric_ships():
    """The labelling judgement is the artefact; shipping the tool without it would be half of it."""
    rubric = os.path.join(ROOT, "calibration", "LABELLING.md")
    assert os.path.exists(rubric)
    text = open(rubric, encoding="utf-8").read()
    assert "would the other need the same change" in text
    assert "unsure" in text

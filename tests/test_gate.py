"""Tests for the optional semantic gate — offline, via a stub judge.

The LLM call itself needs a key and a network; everything that makes the gate *safe* is the
orchestration around it (conservative quorum to clear, surface-the-rest, graceful no-key skip,
deterministic layering). Those are pinned here with a stub judge and need neither.

Run from ratchet-mvp/:  python -m pytest -q  (or python3 tests/run.py)
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import gate

STATES = os.path.join(ROOT, "playground", "_states")


def _stub(*responses):
    """A judge that returns the given JSON strings in order, cycling on the last."""
    box = {"i": 0}

    def judge(_prompt):
        i = min(box["i"], len(responses) - 1)
        box["i"] += 1
        return responses[i]
    return judge


CAT = [{"name": "verb-wrappers", "description": "thin per-verb wrappers"}]


def test_cluster_cleared_on_quorum():
    judge = _stub('{"match": "verb-wrappers", "why": "sanctioned"}')  # every trial agrees
    v = gate._match_cluster(["m.get", "m.post"], "verb", CAT, {}, judge, trials=5, quorum=4)
    assert v["disposition"] == "CLEARED"
    assert v["matched"] == "verb-wrappers"


def test_cluster_surfaces_when_short_of_quorum():
    # 3 match, 2 NONE -> below a quorum of 4 -> surface (conservative: never clear on weak agreement)
    judge = _stub(
        '{"match": "verb-wrappers"}', '{"match": "verb-wrappers"}', '{"match": "verb-wrappers"}',
        '{"match": "NONE"}', '{"match": "NONE"}',
    )
    v = gate._match_cluster(["m.a", "m.b"], "concept", CAT, {}, judge, trials=5, quorum=4)
    assert v["disposition"] == "SURFACE"
    assert v["matched"] is None


def test_cluster_surfaces_on_all_none():
    judge = _stub('{"match": "NONE", "why": "uncatalogued"}')
    v = gate._match_cluster(["m.a", "m.b"], "concept", CAT, {}, judge, trials=5, quorum=4)
    assert v["disposition"] == "SURFACE"


def test_failed_trials_count_as_none_and_surface():
    def judge(_):
        raise RuntimeError("boom")
    v = gate._match_cluster(["m.a", "m.b"], "concept", CAT, {}, judge, trials=3, quorum=2)
    assert v["disposition"] == "SURFACE"  # errors must never clear


def test_deterministic_layer_violation():
    modules = [
        {"module": "util.strings", "depends_on": ["handlers.orders"]},   # util depends UP on handler
        {"module": "handlers.orders", "depends_on": ["services.billing"]},  # fine (down)
    ]
    layer_of = {"util.strings": "util", "handlers.orders": "handler", "services.billing": "service"}
    order = ["handler", "service", "util"]  # high -> low
    viol = gate._deterministic_layer_violations(modules, layer_of, order)
    assert any(v["module"] == "util.strings" and v["kind"] == "up-dependency" for v in viol)
    assert not any(v["module"] == "handlers.orders" for v in viol)


def test_no_key_skips_but_runs_deterministic_layering(monkeypatch=None):
    saved = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        report = gate.run(os.path.join(STATES, "03-loyalty", "billing"), judge=None)
        assert report["skipped"] is True
        assert "ANTHROPIC_API_KEY" in report["reason"]
    finally:
        if saved is not None:
            os.environ["ANTHROPIC_API_KEY"] = saved


def test_run_with_stub_judge_clears_and_surfaces(tmp_path=None):
    import json
    import tempfile

    # a catalogue that blesses "retry" so the retry cluster clears; everything else surfaces
    d = tempfile.mkdtemp()
    cat = os.path.join(d, "catalogue.json")
    with open(cat, "w") as f:
        json.dump({"patterns": [{"name": "retry-family", "description": "sanctioned retry variants"}]}, f)
    judge = _stub('{"match": "retry-family", "why": "blessed"}')  # clears whatever it sees
    report = gate.run(os.path.join(STATES, "03-loyalty", "billing"),
                      catalogue_path=cat, trials=5, quorum=4, judge=judge)
    assert report["skipped"] is False
    assert report["cleared"] >= 1              # the retry cluster cleared
    assert report["cleared"] + report["surfaced"] == len(report["clusters"])

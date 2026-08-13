"""Tests for observed structure, candidates, and separately ratified intent.

Run from ratchet-mvp/:  python -m pytest -q  (or python3 tests/run.py)
"""

import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import selfmodel as sm
from coherence_ratchet import query as q

STATES = os.path.join(ROOT, "playground", "_states")


def _billing(state):
    return os.path.join(STATES, state, "billing")


def test_concept_query_finds_divergent_sites():
    model = sm.derive(_billing("03-loyalty"))
    res = q.answer(model, "which sites compute retry?")
    names = {m["qualname"] for m in res["matches"]}
    # the reinvented retry sites should all surface
    assert any(n.endswith("submit_with_retry") for n in names)
    assert any(n.endswith("export_with_retry") for n in names)
    assert res["candidates"]
    assert all(c["kind"] == "reuse_helper" for c in res["candidates"])


def test_module_structure_uses_bare_names():
    model = sm.derive(_billing("03-loyalty"))
    mod_names = {m["module"] for m in model["observed"]["modules"]}
    fn_mods = {f["module"] for f in model["observed"]["functions"]}
    # module names carry no package prefix, so they line up with function module names
    assert "money" in mod_names
    assert not any(m.startswith("billing.") for m in mod_names)
    assert fn_mods & mod_names  # they share a namespace


def test_derived_model_is_fresh_after_change():
    # RES6: add a new site, re-derive, and it appears with no manual edit to the model.
    with tempfile.TemporaryDirectory() as d:
        pkg = os.path.join(d, "billing")
        os.makedirs(pkg)
        for fn in os.listdir(_billing("03-loyalty")):
            if fn.endswith(".py"):
                with open(os.path.join(_billing("03-loyalty"), fn)) as f:
                    open(os.path.join(pkg, fn), "w").write(f.read())
        before_model = sm.derive(pkg)
        before = {f["qualname"] for f in before_model["observed"]["functions"]}
        with open(os.path.join(pkg, "notifications.py"), "w") as f:
            f.write(
                "import time\n"
                "def notify_with_retry(send, attempts=4, delay=0.1):\n"
                "    err = None\n"
                "    for i in range(attempts):\n"
                "        try:\n"
                "            return send()\n"
                "        except Exception as e:\n"
                "            err = e\n"
                "            time.sleep(delay)\n"
                "    raise err\n"
            )
        after_model = sm.derive(pkg)
        after = {f["qualname"] for f in after_model["observed"]["functions"]}
        new = after - before
        assert any(n.endswith("notify_with_retry") for n in new)
        assert before_model["source"]["tree_hash"] != after_model["source"]["tree_hash"]


def test_entity_intersection_is_observed_evidence_not_canonical_contract():
    with tempfile.TemporaryDirectory() as d:
        pkg = os.path.join(d, "shop")
        os.makedirs(pkg)
        open(os.path.join(pkg, "orders.py"), "w").write(
            'def total(order):\n'
            '    return order["id"], order["lines"], order["customer"]\n'
        )
        open(os.path.join(pkg, "exports.py"), "w").write(
            'def row(order):\n'
            '    return order["id"], order["items"], order["discount"]\n'
        )
        model = sm.derive(pkg)
        res = q.answer(model, "what is the canonical order shape and where does it diverge?")
        assert res["intent"] == "entity"
        order = next(m for m in res["matches"] if m["name"] == "order")
        assert order["keys_observed_at_every_site"] == ["id"]
        assert "canonical_keys" not in order
        assert order["truth"] == "OBSERVED"


def test_model_v2_separates_observed_and_candidates():
    model = sm.derive(_billing("03-loyalty"))
    assert model["schema_version"] == 2
    assert model["source"]["tree_hash"]
    assert model["extractor"]["ruleset_hash"]
    assert model["model_hash"] == sm.model_hash(model)
    assert model["observed"]["functions"]
    assert model["candidates"]
    assert not any("canonical" in str(candidate).lower() for candidate in model["candidates"])


def test_ratification_is_human_owned_and_provenance_bound():
    model = sm.derive(_billing("03-loyalty"))
    candidate = next(c for c in model["candidates"] if c["kind"] == "reuse_helper")
    intent = sm.ratify(
        model, sm.empty_intent(model), candidate["id"], approved_by="architecture-guild",
        rationale="one retry policy at the billing seam", scope="billing",
        approved_at="2026-08-01",
    )
    record = intent["ratifications"][0]
    assert record["approved_by"] == "architecture-guild"
    assert record["candidate_id"] == candidate["id"]
    assert intent["source_model_hash"] == model["model_hash"]


def test_llm_is_optional_and_offline_by_default():
    # With no --llm flag the matcher must be purely deterministic (no network, no key needed).
    model = sm.derive(_billing("00-baseline"))
    res = q.answer(model, "which sites compute retry?", use_llm=False)
    assert res["matcher"] == "deterministic"
    assert "llm" not in res

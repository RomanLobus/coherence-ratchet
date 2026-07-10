"""Tests for the derived self-model and its queries.

Pins the keystone claims: the model is DERIVED (re-deriving after a code change reflects it with no
manual edit — the RES6 freshness property), concept queries find the divergent sites, and the entity
query reports the canonical shape as the contract every site agrees on plus the per-site divergence.

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
    # and a reuse helper is offered
    assert res["helpers"]


def test_module_structure_uses_bare_names():
    model = sm.derive(_billing("03-loyalty"))
    mod_names = {m["module"] for m in model["modules"]}
    fn_mods = {f["module"] for f in model["functions"]}
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
        before = {f["qualname"] for f in sm.derive(pkg)["functions"]}
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
        after = {f["qualname"] for f in sm.derive(pkg)["functions"]}
        new = after - before
        assert any(n.endswith("notify_with_retry") for n in new)


def test_entity_canonical_is_shared_contract_and_reports_divergence():
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
        # only "id" is in every site -> that is the shared contract
        assert order["canonical_keys"] == ["id"]
        # each site's non-shared keys are reported as divergence
        assert order["divergent_sites"]


def test_llm_is_optional_and_offline_by_default():
    # With no --llm flag the matcher must be purely deterministic (no network, no key needed).
    model = sm.derive(_billing("00-baseline"))
    res = q.answer(model, "which sites compute retry?", use_llm=False)
    assert res["matcher"] == "deterministic"
    assert "llm" not in res

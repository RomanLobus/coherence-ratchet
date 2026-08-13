"""The dispatcher turns a recorded run into one somebody else can check.

The tests use an injected transport, so the whole pipeline is exercised without a network call or a
key. What they pin is not the model's behaviour — that is the experiment's job — but the properties
that decide whether a promoted write-up is worth anything: the model is pinned to a dated snapshot,
a failed trial is recorded rather than dropped, the raw response is kept so scoring can be re-run
offline for ever, and a later edit to the probe is detectable rather than silent.
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "experiments"))

from harness import DispatchRefused, dispatch, load_probe, rescore  # noqa: E402
from harness.dispatch import extract_code, verify  # noqa: E402

PROBE = os.path.join(ROOT, "probe_fullcontext_fragmentation.py")
DATED = "claude-haiku-4-5-20251001"

_REUSE = (
    "```python\n"
    "from billing.money import to_cents\n"
    "from billing.retry import retry\n"
    "def charge_customer(order, gateway):\n"
    "    return retry(lambda: gateway.submit(order['id'], to_cents(order['amount'])))\n"
    "```"
)


def _probe():
    return load_probe(PROBE)


def _transport(text=_REUSE, fail_on=()):
    calls = {"n": 0}

    def transport(prompt, *, model, temperature, max_tokens):
        calls["n"] += 1
        if calls["n"] in fail_on:
            raise RuntimeError("upstream said no")
        return json.dumps({"content": [{"type": "text", "text": text}]})

    transport.calls = calls
    return transport


# --- the pin ----------------------------------------------------------------

def test_an_undated_model_alias_is_refused():
    """An alias points at a moving target, so the run could not be compared with a later one."""
    try:
        dispatch(_probe(), ["task_only"], trials=1, model="claude-haiku-4-5",
                 out_dir=tempfile.mkdtemp(), transport=_transport())
    except DispatchRefused as exc:
        assert "alias" in str(exc)
        return
    raise AssertionError("an alias was accepted")


def test_a_missing_model_is_refused():
    try:
        dispatch(_probe(), ["task_only"], trials=1, model="", out_dir=tempfile.mkdtemp(),
                 transport=_transport())
    except DispatchRefused:
        return
    raise AssertionError("a run with no model was accepted")


def test_the_manifest_pins_everything_a_rerun_needs():
    out = tempfile.mkdtemp()
    manifest = dispatch(_probe(), ["task_only"], trials=2, model=DATED, out_dir=out,
                        transport=_transport(), now="2026-08-11T00:00:00Z")

    for key in ("probe_module", "probe_sha256", "prompt_sha256", "model", "temperature",
                "max_tokens", "trials", "started_at", "harness_version"):
        assert manifest.get(key) is not None, key
    assert manifest["model"] == DATED
    on_disk = json.load(open(os.path.join(out, "manifest.json")))
    assert on_disk["prompt_sha256"]["task_only"]


# --- the evidence -----------------------------------------------------------

def test_raw_responses_are_kept_so_scoring_can_be_rerun_without_a_key():
    out = tempfile.mkdtemp()
    dispatch(_probe(), ["task_only"], trials=2, model=DATED, out_dir=out,
             transport=_transport(), now="2026-08-11T00:00:00Z")
    files = sorted(os.listdir(os.path.join(out, "task_only")))

    assert "trial-00.raw.json" in files
    assert "trial-00.extracted.py" in files

    # Re-scoring touches no transport at all.
    scored = rescore(_probe(), out)
    assert len(scored["scores"]["task_only"]) == 2
    assert os.path.exists(os.path.join(out, "scores.json"))


def test_the_deterministic_scorer_reads_the_persisted_code():
    out = tempfile.mkdtemp()
    dispatch(_probe(), ["task_only"], trials=2, model=DATED, out_dir=out,
             transport=_transport(_REUSE), now="2026-08-11T00:00:00Z")

    scores = rescore(_probe(), out)["scores"]["task_only"]
    assert all(s["reuse_cents"] for s in scores)
    assert not any(s["reinvent_cents"] for s in scores)


def test_a_failed_trial_is_recorded_not_dropped():
    """Dropping it would quietly change the denominator, which is how a sample size lies."""
    out = tempfile.mkdtemp()
    manifest = dispatch(_probe(), ["task_only"], trials=3, model=DATED, out_dir=out,
                        transport=_transport(fail_on=(2,)), now="2026-08-11T00:00:00Z")

    assert manifest["errors"]["task_only"][0]["trial"] == 1
    assert len(rescore(_probe(), out)["scores"]["task_only"]) == 2


def test_a_completed_trial_is_never_rebilled():
    out = tempfile.mkdtemp()
    first = _transport()
    dispatch(_probe(), ["task_only"], trials=3, model=DATED, out_dir=out, transport=first,
             now="2026-08-11T00:00:00Z")
    second = _transport()
    dispatch(_probe(), ["task_only"], trials=3, model=DATED, out_dir=out, transport=second,
             now="2026-08-11T00:00:00Z")

    assert first.calls["n"] == 3
    assert second.calls["n"] == 0


# --- drift ------------------------------------------------------------------

def test_a_probe_edit_after_the_run_is_detectable():
    """A prompt edit invalidates a comparison, and silence about it is the failure mode."""
    out = tempfile.mkdtemp()
    dispatch(_probe(), ["task_only"], trials=1, model=DATED, out_dir=out,
             transport=_transport(), now="2026-08-11T00:00:00Z")
    assert verify(_probe(), out)["prompt_drift"] == {}

    manifest_path = os.path.join(out, "manifest.json")
    manifest = json.load(open(manifest_path))
    manifest["prompt_sha256"]["task_only"] = "0" * 64
    json.dump(manifest, open(manifest_path, "w"))

    assert "task_only" in verify(_probe(), out)["prompt_drift"]


# --- dry run ----------------------------------------------------------------

def test_dry_run_prices_the_sweep_and_spends_nothing():
    transport = _transport()
    result = dispatch(_probe(), ["task_only", "full_surfaced"], trials=10, model=DATED,
                      out_dir="", transport=transport, dry_run=True)

    assert result["calls"] == 20
    assert result["approx_prompt_tokens"] > 0
    assert transport.calls["n"] == 0


# --- the probe contract -----------------------------------------------------

def test_a_module_without_build_prompt_is_refused():
    path = os.path.join(tempfile.mkdtemp(), "not_a_probe.py")
    with open(path, "w") as f:
        f.write("VALUE = 1\n")
    try:
        load_probe(path)
    except DispatchRefused as exc:
        assert "build_prompt" in str(exc)
        return
    raise AssertionError("a module with no build_prompt was accepted")


def test_code_is_extracted_from_a_fenced_block():
    assert extract_code("prose\n```python\nx = 1\n```\nmore").strip() == "x = 1"
    # A model that returns bare code is not silently scored as empty.
    assert extract_code("x = 1").strip() == "x = 1"

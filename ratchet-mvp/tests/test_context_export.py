"""Tests for the self-model context export (the agent-grounding pack)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import selfmodel as sm

STATE = os.path.join(ROOT, "playground", "_states", "03-loyalty", "billing")


def test_context_pack_labels_candidates_without_commanding_reuse():
    pack = sm.context_pack(sm.derive(STATE))
    assert "[CANDIDATE]" in pack
    assert "not instructions" in pack
    assert "Apply `" not in pack


def test_context_pack_lists_observed_module_dependencies():
    pack = sm.context_pack(sm.derive(STATE))
    assert "[OBSERVED]" in pack
    assert "money" in pack


def test_only_ratified_intent_is_imperative():
    model = sm.derive(STATE)
    candidate = next(c for c in model["candidates"] if c["kind"] == "reuse_helper")
    intent = sm.ratify(
        model, sm.empty_intent(model), candidate["id"], approved_by="steward",
        rationale="reviewed against retry semantics", approved_at="2026-08-01",
        scope="billing",
    )
    pack = sm.context_pack(model, intent)
    assert "[RATIFIED] Apply" in pack
    assert "Approved by steward" in pack


def test_context_pack_is_nonempty_markdown():
    pack = sm.context_pack(sm.derive(STATE))
    assert pack.startswith("# Coherence grounding pack")
    assert len(pack.splitlines()) > 5

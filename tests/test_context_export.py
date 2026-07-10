"""Tests for the self-model context export (the agent-grounding pack)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from coherence_ratchet import selfmodel as sm

STATE = os.path.join(ROOT, "playground", "_states", "03-loyalty", "billing")


def test_context_pack_surfaces_reuse_helpers():
    pack = sm.context_pack(sm.derive(STATE))
    assert "Reuse these canonical helpers" in pack
    assert "retry.retry" in pack           # the canonical retry helper is surfaced by name
    assert "reuse" in pack.lower()


def test_context_pack_lists_module_layers():
    pack = sm.context_pack(sm.derive(STATE))
    assert "Module layers" in pack
    assert "money" in pack


def test_context_pack_is_nonempty_markdown():
    pack = sm.context_pack(sm.derive(STATE))
    assert pack.startswith("# Coherence self-model")
    assert len(pack.splitlines()) > 5

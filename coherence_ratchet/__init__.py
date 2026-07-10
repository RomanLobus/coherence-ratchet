"""The coherence ratchet — deterministic MVP.

A coherence metric that can only hold or tighten, the way a coverage or lint
ratchet works, applied to design redundancy and coupling. No LLM in the loop.
"""

from .metrics import Snapshot, measure
from .ratchet import Budget, check, init_budget, tighten, append_ledger
from .signals import Composite, measure_all, connascence_of_meaning, hyperliminal

__all__ = [
    "Snapshot",
    "measure",
    "Composite",
    "measure_all",
    "connascence_of_meaning",
    "hyperliminal",
    "Budget",
    "check",
    "init_budget",
    "tighten",
    "append_ledger",
]

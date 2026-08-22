"""Probe: the constrained catalogue-matcher, on the eight `requests` clusters.

`gate-generalisation.md` recorded the gate disposing every cluster correctly across three libraries
with no dangerous false-clear. Its catalogues and its ground-truth labels were never committed, so
that figure has stayed `RECORDED_RUN` and Appendix C no longer prints it. This probe is what can be
built instead: the same framing, run against the committed cluster fixture and the reconstructed
catalogue, whose own `_note` says a run against it "is a new experiment with its own date, not a
replication of the old one". That is what this is.

The framing is the one that survived, and it is not the subjective judge in `probe_gate_judge.py`:
judge only by the catalogue, return a pattern's exact name or NONE, never invent a name.

Two things are scored, and keeping them apart is the point.

**Catalogue fidelity** needs no oracle. A returned name either is an exact entry in the catalogue or
it is not, and a name that is not is wrong however anybody would have labelled the cluster. This is
the half that can carry a claim.

**Agreement with the hand labels** is reported as agreement and never as correctness. The labels in
`probe_gate_judge.py` were assigned by one person with no written rubric, which is recorded above
`CLUSTERS` there. A disagreement between this gate and those labels is a disagreement, and calling it
an error would smuggle the weak oracle back in through a probe built to replace a figure that rested
on it.
"""

from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from probe_gate_judge import CLUSTERS, _member_source  # noqa: E402

CATALOGUE_PATH = os.path.join(HERE, "coherence", "catalogues", "requests-catalogue.json")

with open(CATALOGUE_PATH, encoding="utf-8") as _f:
    CATALOGUE = json.load(_f)

PATTERN_NAMES = tuple(p["name"] for p in CATALOGUE["patterns"])

CONDITIONS = tuple(CLUSTERS)

# The harness passes CANONICAL_NAMES[condition] to the scorer positionally, and this scorer needs to
# know which cluster it is scoring in order to look the label up. Declaring the cluster id as its own
# canonical name is how a per-condition scorer gets its condition.
CANONICAL_NAMES = {cid: (cid,) for cid in CONDITIONS}

_CATALOGUE_TEXT = "\n".join(
    f"- {p['name']}: {p['description']}" for p in CATALOGUE["patterns"]
)

_SCHEMA = (
    "Answer with JSON and nothing else, in exactly this shape:\n"
    '{"pattern": "<the exact name of one catalogue entry, or NONE>", '
    '"reason": "<one sentence>", "confidence": "low" | "medium" | "high"}'
)


def build_prompt(condition: str) -> str:
    cluster = CLUSTERS[condition]
    bodies = "\n\n".join(
        f"# {m}\n{_member_source(m)}".rstrip() for m in cluster["members"]
    )
    return (
        "These functions were grouped as near-duplicates by a structural detector in a Python "
        "library.\n\n"
        f"{bodies}\n\n"
        "Below is the library's catalogue of sanctioned patterns. It is the only authority you may "
        "use.\n\n"
        f"{_CATALOGUE_TEXT}\n\n"
        "Decide whether this group is an instance of exactly one catalogue entry. If it is, return "
        "that entry's name exactly as written above. If it is not, or you are unsure, return NONE. "
        "Do not invent a pattern name and do not judge from your own view of good design.\n\n"
        f"{_SCHEMA}"
    )


_JSON = re.compile(r"\{.*\}", re.S)

# A cluster the labels call SANCTIONED is one the catalogue should be able to clear; a cluster they
# call CONSOLIDATE is one it should refuse. "Dangerous" names the asymmetry: clearing something the
# labels say needed consolidating is the failure that ships, and refusing something they say was fine
# only costs a person a look.
_LABEL_CLEARS = {"SANCTIONED": True, "CONSOLIDATE": False}


def score_code(text: str, condition: str = "", *_names) -> dict:
    match = _JSON.search(text or "")
    payload = None
    if match:
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            payload = None
    if not isinstance(payload, dict):
        return {"pattern": None, "parsed": False, "in_catalogue": False,
                "cleared": False, "hallucinated_name": False}

    raw = str(payload.get("pattern", "")).strip()
    is_none = raw.upper() == "NONE" or raw == ""
    in_catalogue = raw in PATTERN_NAMES
    cleared = in_catalogue and not is_none

    out = {
        "pattern": None if is_none else raw,
        "parsed": True,
        "confidence": payload.get("confidence"),
        "reason": payload.get("reason"),
        # Objective: a returned name that is not a catalogue entry is wrong without any oracle.
        "in_catalogue": in_catalogue or is_none,
        "hallucinated_name": not is_none and not in_catalogue,
        "cleared": cleared,
    }

    label = CLUSTERS.get(condition, {}).get("ground_truth")
    if label in _LABEL_CLEARS:
        should_clear = _LABEL_CLEARS[label]
        out["label"] = label
        out["agrees_with_label"] = (cleared == should_clear)
        # Reported separately because the asymmetry is what the design cares about.
        out["cleared_against_label"] = cleared and not should_clear
    return out

"""Consume another tool's measurement, so the loop is not limited to what this extractor parses.

The reference extractor reads Python. The judgement does not: ratifying intent, assessing exposure,
holding a regional line and deciding at a seam are language-neutral, and the only thing tying them to
Python is where the counts come from. This module takes the counts from somewhere else.

Two rules make that safe, and both are refusals rather than conventions.

**Raw counts only; ratios are computed here and never accepted from a producer.** A composite score
with a growing denominator falls while the raw counts hold, which is the dilution failure the pawl
exists to refuse. A producer that offers a score and no counts cannot be ratcheted honestly, so an
import that finds only a score is refused and says why.

**Everything imported is a candidate, never an observation.** This tool did not read that code. It is
repeating what another tool reported, and the provenance travels with it: producer, producer version,
and the producer schema version this adapter was written against. A grounding pack built on imported
facts therefore names the parser that produced them.

The adapter is pinned to a declared producer schema version and fails loudly when it meets another.
A fast-moving producer must break this visibly rather than degrade into a quiet mismeasurement.
"""

from __future__ import annotations

import json
import os
import sys

from .exitcodes import EXIT_HELD, EXIT_REFUSED

MEASUREMENT_SCHEMA = "coherence-measurement/1"

# The producer schema versions this adapter has been read against and tested on. A different
# version is refused by number rather than guessed at.
SUPPORTED_PRODUCERS = {
    "drift": {"key": "baseline_version", "versions": (1,)},
}


class ImportRefused(Exception):
    """The producer's output cannot be turned into an honest measurement."""


class Measurement:
    """Imported counts, in the shape the ratchet already consumes.

    ``to_dict`` returns metric names to raw counts, which is all ``Budget.breaches`` needs. The
    names are namespaced by producer so an imported signal can never be confused with one this
    tool measured itself.
    """

    def __init__(self, counts: dict[str, float], meta: dict):
        self.counts = dict(counts)
        self.meta = dict(meta)

    def to_dict(self) -> dict:
        return dict(self.counts)

    def as_json(self) -> dict:
        return {
            "schema": MEASUREMENT_SCHEMA,
            "produced_by": self.meta.get("produced_by", {}),
            "source": self.meta.get("source", {}),
            "epistemic": "candidate",
            "counts": {k: {"raw": v, "unit": "findings"} for k, v in sorted(self.counts.items())},
            "sites": self.meta.get("sites", []),
        }


def _read_json(path: str) -> dict:
    if not os.path.exists(path):
        raise ImportRefused(f"{path} does not exist")
    try:
        # Producers written on Windows toolchains emit a BOM; drift's own committed baseline does.
        with open(path, encoding="utf-8-sig") as handle:
            return json.load(handle)
    except (OSError, ValueError) as exc:
        raise ImportRefused(f"{path} is not readable JSON: {exc}") from exc


def read_drift(path: str) -> Measurement:
    """Turn a `drift` baseline or report into a measurement of raw counts."""
    doc = _read_json(path)
    spec = SUPPORTED_PRODUCERS["drift"]
    version = doc.get(spec["key"])
    if version is None:
        raise ImportRefused(
            f"{path} carries no {spec['key']}, so it is not a drift baseline this adapter can read. "
            "Produce one with `drift analyze --repo . --format json`."
        )
    if version not in spec["versions"]:
        supported = ", ".join(str(v) for v in spec["versions"])
        raise ImportRefused(
            f"{path} declares {spec['key']}={version}; this adapter was written against "
            f"{spec['key']} {supported}. Refusing to guess at a schema it has not been read "
            "against: a silently mismapped signal is worse than a failed import."
        )

    findings = doc.get("findings")
    if not isinstance(findings, list):
        score = doc.get("drift_score")
        detail = f" It reports drift_score={score} and no findings." if score is not None else ""
        raise ImportRefused(
            f"{path} carries no per-finding records, so only a composite score is on offer.{detail} "
            "A score cannot be ratcheted honestly: it falls when the codebase grows while the raw "
            "counts hold, which is the dilution this tool's pawl exists to refuse. Re-export with "
            "findings included."
        )

    counts: dict[str, float] = {}
    sites = []
    for item in findings:
        signal = item.get("signal")
        if not signal:
            continue
        key = f"drift.{signal}"
        counts[key] = counts.get(key, 0) + 1
        sites.append({
            "signal": key,
            "file": item.get("file"),
            "line": item.get("start_line"),
            "title": item.get("title"),
            "fingerprint": item.get("fingerprint"),
        })

    if not counts:
        raise ImportRefused(
            f"{path} lists findings but none carries a signal name, so there is nothing to count."
        )

    declared = doc.get("finding_count")
    if isinstance(declared, int) and declared != len(findings):
        # A producer disagreeing with itself is a reason to stop, not to pick a number.
        raise ImportRefused(
            f"{path} declares finding_count={declared} and carries {len(findings)} findings. "
            "Refusing to choose between them."
        )

    return Measurement(counts, {
        "produced_by": {
            "tool": "drift",
            "version": doc.get("drift_version", "unknown"),
            "producer_schema": f"{spec['key']}={version}",
            "adapter": MEASUREMENT_SCHEMA,
        },
        "source": {
            "created_at": doc.get("created_at"),
            "scope": doc.get("drift_score_scope"),
        },
        "sites": sites,
    })


ADAPTERS = {"drift": read_drift}


def load_measurement(path: str) -> Measurement:
    """Read a measurement this tool wrote earlier."""
    doc = _read_json(path)
    if doc.get("schema") != MEASUREMENT_SCHEMA:
        raise ImportRefused(
            f"{path} declares schema {doc.get('schema')!r}, not {MEASUREMENT_SCHEMA!r}."
        )
    counts = {}
    for name, entry in (doc.get("counts") or {}).items():
        if not isinstance(entry, dict) or "raw" not in entry:
            raise ImportRefused(
                f"{path}: {name} carries no raw count. This schema takes raw counts only, "
                "because a ratio cannot be ratcheted without the numerator behind it."
            )
        counts[name] = entry["raw"]
    if not counts:
        raise ImportRefused(f"{path} carries no counts.")
    return Measurement(counts, {k: doc.get(k) for k in ("produced_by", "source", "sites")})


def budget_from_measurement(measurement: Measurement, *, author: str, reason: str | None,
                            set_at: str | None, prior: dict | None = None):
    """Baseline ceilings from imported counts.

    Every imported signal is watched, rather than the fixed WATCHED set: this tool has no opinion
    about which of another producer's signals matter, and silently dropping the ones it does not
    recognise would baseline a portfolio narrower than the reader thinks they set.

    Imported ceilings carry no numerators, and need none. These are raw counts, and a raw count
    cannot be diluted by a growing denominator, which is the one thing the pawl guards against.
    """
    from .ratchet import Budget

    provenance = {"author": author, "imported_from": measurement.meta.get("produced_by", {})}
    if reason is not None:
        provenance["reason"] = reason
    if set_at is not None:
        provenance["set_at"] = set_at
    if prior:
        provenance["prior"] = prior
    return Budget(ceilings=dict(measurement.counts), numerators={}, provenance=provenance)


# --- CLI --------------------------------------------------------------------

def register_cli(sub) -> None:
    p = sub.add_parser(
        "import",
        help="read another tool's measurement as candidate counts (drift)",
    )
    p.add_argument("producer", choices=sorted(ADAPTERS), help="the tool that produced the file")
    p.add_argument("file", help="the producer's JSON output")
    p.add_argument("--out", default="coherence/measurement.json")
    p.add_argument("--quiet", action="store_true")


def run_cli(args) -> int:
    try:
        measurement = ADAPTERS[args.producer](args.file)
    except ImportRefused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return EXIT_REFUSED

    directory = os.path.dirname(args.out)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(measurement.as_json(), handle, indent=2, sort_keys=False)
        handle.write("\n")

    if not args.quiet:
        produced = measurement.meta.get("produced_by", {})
        print(f"imported {sum(measurement.counts.values()):g} findings from "
              f"{produced.get('tool')} {produced.get('version')} -> {args.out}")
        for name, value in sorted(measurement.counts.items()):
            print(f"  {name} {value:g}")
        print("\nThese are candidates, not observations: this tool did not read that code, and "
              "the producer is recorded with the counts. Ratify nothing on their strength without "
              "reading the sites.")
    return EXIT_HELD

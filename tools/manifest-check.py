#!/usr/bin/env python3
"""Bind the lab's recorded result to the artefacts that produced it.

`manifest.json` used to hash the lab's *inputs* -- four contracts, two producers, the lockfile -- and
none of the machinery that turns them into a verdict. So `verify.sh`, which is the oracle, could be
edited to assert nothing at all, and the lab would still print "Enterprise seam lab passed." with every
recorded hash matching and `status: VERIFIED` untouched. `producer/emit.py` chooses the test input,
`consumer/src/test-consumer.ts` carries the assertion, and `consumer/package.json` decides which
contract the types are generated from. None was hashed. The recorded detail, "REFUTED at five
milli-cents: expected one cent, received zero", comes entirely from two of those unhashed files.

The idiom is borrowed from the probe harness rather than invented: `ratchet-mvp/experiments/harness/
dispatch.py` records `probe_sha256` from the probe's own source, so a run is pinned to the code that
produced it, and its `verify()` reports drift rather than assuming none. This is the same thing for a
lab whose oracle is a shell script.

Two modes:

    check    every listed artefact exists and matches, and every relevant file is listed (default)
    refresh  rewrite the hashes from disk, for use when a change is intended

`refresh` is deliberately a separate verb. A checker that silently rewrites what it is checking is not
a checker.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

# Each lab declares its own pins, in its own manifest, under a `pins` object:
#
#     "pins": {
#       "inputs": ["contracts/baseline.yaml", ...],
#       "oracle": ["verify.sh", "producer/emit.py", ...],
#       "derived": ["consumer/src/generated/schema.d.ts"]
#     }
#
# `inputs` is what the run is about. `oracle` is what decides the verdict, and is the half both labs
# were missing. `derived` is regenerated from a pinned input on every run, so it is deliberately not
# hashed and is listed only so the omission is on the record rather than implied.


def sha256(lab: str, rel: str) -> str:
    with open(os.path.join(lab, rel), "rb") as stream:
        return hashlib.sha256(stream.read()).hexdigest()


def source_revision(lab: str) -> str | None:
    try:
        done = subprocess.run(["git", "rev-parse", "HEAD"], cwd=lab,
                              capture_output=True, text=True, check=False)
    except OSError:
        return None
    return done.stdout.strip() or None


def _pins(manifest: dict) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    pins = manifest.get("pins") or {}
    inputs = tuple(pins.get("inputs") or ())
    oracle = tuple(pins.get("oracle") or ())
    derived = tuple(pins.get("derived") or ())
    if not inputs and not oracle:
        raise SystemExit("manifest declares no `pins`; add one naming its inputs and its oracle")
    return inputs, oracle, derived


def check(lab: str) -> int:
    with open(os.path.join(lab, "manifest.json"), encoding="utf-8") as stream:
        manifest = json.load(stream)
    INPUTS, ORACLE, DERIVED = _pins(manifest)
    REQUIRED = INPUTS + ORACLE
    listed = {entry["path"]: entry["sha256"] for entry in manifest.get("artefacts", [])}
    problems = []

    for rel in REQUIRED:
        if rel not in listed:
            problems.append(f"not pinned by the manifest: {rel}")
            continue
        if not os.path.exists(os.path.join(lab, rel)):
            problems.append(f"pinned but missing from disk: {rel}")
            continue
        actual = sha256(lab, rel)
        if actual != listed[rel]:
            problems.append(f"changed since it was verified: {rel}\n"
                            f"      recorded {listed[rel]}\n      on disk  {actual}")

    for rel in listed:
        if rel not in REQUIRED and rel not in DERIVED:
            problems.append(f"pinned but not in the required set, so the set is stale: {rel}")

    if problems:
        print("manifest does not bind this lab's result:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print("\nIf the change is intended, re-verify the lab and run:\n"
              f"  python3 tools/manifest-check.py {os.path.relpath(lab)} refresh", file=sys.stderr)
        return 1

    print(f"manifest binds {len(REQUIRED)} artefacts, all matching "
          f"({len(INPUTS)} inputs, {len(ORACLE)} oracle).")
    return 0


def refresh(lab: str) -> int:
    path = os.path.join(lab, "manifest.json")
    with open(path, encoding="utf-8") as stream:
        manifest = json.load(stream)
    INPUTS, ORACLE, _ = _pins(manifest)
    REQUIRED = INPUTS + ORACLE
    manifest["artefacts"] = [{"path": rel, "sha256": sha256(lab, rel)} for rel in REQUIRED]
    revision = source_revision(lab)
    if revision:
        manifest["source_revision"] = revision
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
    print(f"manifest refreshed: {len(REQUIRED)} artefacts"
          + (f", source_revision {revision[:12]}" if revision else ""))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"usage: {sys.argv[0]} <lab-directory> [check|refresh]", file=sys.stderr)
        raise SystemExit(2)
    lab = os.path.abspath(sys.argv[1])
    mode = sys.argv[2] if len(sys.argv) > 2 else "check"
    if mode not in ("check", "refresh"):
        print(f"usage: {sys.argv[0]} <lab-directory> [check|refresh]", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(check(lab) if mode == "check" else refresh(lab))

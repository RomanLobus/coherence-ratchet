#!/usr/bin/env python3
"""Turn a local `history` dump into a registry submission, and say what was removed.

Anonymisation a submitter cannot inspect is a promise, not a property. This runs on their machine,
prints every field it strips, and writes a file they can read in full before deciding to send it.

    coherence-ratchet history <subsystem> --repo . --samples 24 --json reading.json
    python3 registry/anonymise.py reading.json --key my-billing-slice \\
        --language python --size "50-200 modules" --authorship some \\
        --estimated-by "co-authored-by trailers on ~40% of commits since March"

Nothing is uploaded. The output is a file; sending it is a separate, deliberate act.
"""

import argparse
import json
import os
import sys

SCHEMA = "coherence-reader-reading/1"
KEEP = ("mods", "edges", "cyclic_modules", "unreadable_modules", "cycle_ratio", "coupling", "instab")
# Fields that identify a repository exactly, or narrow it to a handful.
STRIP_POINT = ("sha", "date")
STRIP_TOP = ("library", "clone", "src_candidates", "first", "last", "shas", "commits_total")


def main() -> int:
    ap = argparse.ArgumentParser(description="Prepare a reader-registry submission from a history dump.")
    ap.add_argument("dump", help="the JSON written by `coherence-ratchet history --json`")
    ap.add_argument("--key", required=True, help="an opaque project key you choose and keep")
    ap.add_argument("--language", required=True)
    ap.add_argument("--size", required=True,
                    choices=["<50 modules", "50-200 modules", "200-1000 modules", ">1000 modules"])
    ap.add_argument("--authorship", required=True,
                    choices=["none", "some", "about half", "most", "nearly all"])
    ap.add_argument("--estimated-by", required=True, help="how you arrived at that band")
    ap.add_argument("--note", default="")
    ap.add_argument("--out", default="submission.json")
    args = ap.parse_args()

    with open(args.dump, encoding="utf-8") as fh:
        dump = json.load(fh)

    removed: list[str] = []
    for field in STRIP_TOP:
        if field in dump:
            removed.append(f"{field} = {json.dumps(dump[field])[:70]}")

    points = []
    for p in dump.get("points", []):
        if "error" in p:
            continue
        for field in STRIP_POINT:
            if field in p and field == "sha":
                removed.append(f"points[].sha = {p[field][:12]}…")
        out = {"month": (p.get("date") or "")[:7]}
        out.update({k: p[k] for k in KEEP if k in p})
        if not out["month"]:
            print("refused: a point carries no date, so its month cannot be recorded", file=sys.stderr)
            return 2
        points.append(out)

    if len(points) < 2:
        print("refused: fewer than two measured points; a single reading is not a curve", file=sys.stderr)
        return 2

    analyser = dump.get("analyser") or {}
    missing = [k for k in ("version", "source_sha256_16", "python") if k not in analyser]
    if missing:
        print(f"refused: the dump does not stamp {', '.join(missing)}. Two submissions are only "
              "comparable if the analyser and interpreter are recorded; re-run with a current "
              "coherence-ratchet.", file=sys.stderr)
        return 2

    submission = {
        "schema": SCHEMA,
        "project_key": args.key,
        "language": args.language,
        "size_band": args.size,
        "agent_authorship": {"band": args.authorship, "estimated_by": args.estimated_by},
        "analyser": {k: analyser[k] for k in ("version", "source_sha256_16", "python")},
        "points": points,
    }
    if args.note:
        submission["note"] = args.note

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(submission, fh, indent=2)
        fh.write("\n")

    print(f"wrote {args.out} — {len(points)} points, {os.path.getsize(args.out)} bytes")
    print("\nremoved, and not present in the output:")
    for line in dict.fromkeys(removed):
        print(f"  {line}")
    print("\nRead the file before sending it. Nothing has been uploaded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

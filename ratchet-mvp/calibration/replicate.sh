#!/bin/sh
# Re-derive the calibration corpus and re-score the labels, offline.
#
# Two things are checked, and they fail for different reasons:
#
#   1. The corpus reproduces. `calibrate sample` is deterministic given a seed and a source
#      revision, so re-sampling the pinned revisions must reproduce `pairs.jsonl` pair for pair.
#      A difference means the sampler changed, and every number scored from the old corpus is
#      stale. This step needs the four clones and is skipped without them.
#
#   2. The labels still score to the same table. This is deterministic and needs no network,
#      so CI runs it on every commit: the labelled corpus plus the scorer must reproduce
#      `results.txt` byte for byte. A difference means the scorer changed under a published
#      figure.
#
# Usage:
#   calibration/replicate.sh                 # score only (offline, what CI runs)
#   CLONE_ROOT=/path calibration/replicate.sh --with-corpus
set -eu

here="$(cd "$(dirname "$0")" && pwd)"
root="$(dirname "$here")"
clone_root="${CLONE_ROOT:-/tmp/coherence-arch-clones}"
labelled="$here/pairs-labelled.jsonl"
results="$here/results.txt"
fail=0

if [ ! -f "$labelled" ]; then
  echo "calibration: no labels yet ($labelled absent)."
  echo "  Build the labelling page and label the corpus:"
  echo "    python3 calibration/build_labeller.py && open calibration/label.html"
  echo "  Nothing to replicate until then; this is not a failure."
  exit 0
fi

echo "== labels re-scored =="
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
( cd "$root" && python3 -m coherence_ratchet.cli calibrate score "$labelled" ) > "$tmp/results.now" 2>&1

if [ -f "$results" ]; then
  if diff -u "$results" "$tmp/results.now"; then
    echo "  ok: the published table reproduces from the committed labels"
  else
    echo "FAIL: the scored table no longer matches $results"
    fail=1
  fi
else
  cp "$tmp/results.now" "$results"
  echo "  wrote $results (first run)"
fi

if [ "${1:-}" = "--with-corpus" ]; then
  echo "== corpus re-derived from the pinned revisions =="
  ( cd "$root" && python3 - "$clone_root" ) <<'PY'
import json, os, subprocess, sys
sys.path.insert(0, os.getcwd())
from coherence_ratchet.calibrate import sample

clone_root = sys.argv[1]
prov = json.load(open("calibration/provenance.json"))
roots = {"requests": "requests/src/requests", "flask": "flask/src/flask",
         "boltons": "boltons/boltons", "httpie": "httpie/httpie"}
missing = [k for k, v in roots.items() if not os.path.isdir(os.path.join(clone_root, v))]
if missing:
    print(f"  skipped: clones absent for {', '.join(missing)} (set CLONE_ROOT)")
    raise SystemExit(0)

for lib, sha in prov["revisions"].items():
    at = subprocess.run(["git", "-C", os.path.join(clone_root, roots[lib].split("/")[0]),
                         "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if at != sha:
        print(f"  FAIL: {lib} clone is at {at[:12]}, corpus was sampled at {sha[:12]}")
        raise SystemExit(1)

fresh = []
for lib in roots:
    rows = sample(os.path.join(clone_root, roots[lib]), n=prov["n_per_library"], seed=prov["seed"])
    for r in rows:
        r["library"] = lib
    fresh.extend(rows)
fresh.sort(key=lambda r: (-r["jaccard"], r["library"]))
committed = [json.loads(l) for l in open("calibration/pairs.jsonl")]
key = lambda r: (r["library"], r["a"], r["b"])
if [key(r) for r in fresh] != [key(r) for r in committed]:
    print("  FAIL: re-sampling the pinned revisions did not reproduce pairs.jsonl")
    raise SystemExit(1)
print(f"  ok: {len(fresh)} pairs reproduce from the pinned revisions")
PY
fi

[ "$fail" -eq 0 ] || exit 1
echo "calibration replicate clean."

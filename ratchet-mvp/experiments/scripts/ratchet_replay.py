"""Ratchet replay — would a delta ratchet have flagged the measured decay?

Answers Chapter 8's "would it have mattered?" against the same pinned commits that produced
the architecture curves, so the replay and the curves report one universe rather than two.

Why this script exists
----------------------
The replay counts quoted in early drafts (43, 49 and 50 intervals per library) came from an
uncommitted dense sweep whose script and data were never retained, and they contradicted the
frozen-share flag counts in Appendix A.13, which came from `probe_volatility_ratchet.py`'s
*unpinned* 16-sample sweep. Unpinned even-index sampling over a growing history is
epoch-dependent: the same code run months later samples different commits and prints different
digits, which is the reason `longitudinal_arch.py` pins its SHAs in the first place.

This script removes both problems. It reads the pinned SHAs from
`experiments/longitudinal_arch_pins.json` — the same commits behind every printed curve — and
reports the raw and the volatility-gated flag counts together.

The rules, stated so the counts are checkable
---------------------------------------------
  * SAMPLES are the 16 pinned commits per library. A sample whose package directory does not
    exist yet is EXCLUDED, not scored as zero: structure that is not there cannot be measured,
    and treating an absent package as a clean zero would invent a backsliding interval at the
    moment the package first appears. Excluded samples are reported per library.
  * RAW FLAG on interval (t -> t+1): cycle_ratio(t+1) > cycle_ratio(t). This is the baseline
    delta ratchet — the same rule `probe_volatility_ratchet.py` states.
  * GATED FLAG applies Appendix A.13's frozen-share gate: keep a raw flag only if at least one
    module that NEWLY enters a cycle at t+1 has volatility > FROZEN_THRESHOLD. A raw flag whose
    newly-cyclic modules are all frozen is suppressed as `all-frozen`; a raw flag where the ratio
    rose with no module newly entering a cycle is suppressed as `denominator-shift` — the ratio
    moved because the denominator shrank, which is Chapter 3's denominator warning firing inside
    the ratchet's own instrument.
  * VOLATILITY(m) is m's max-normalised commit count over the ancestry of the LAST PINNED
    commit, read at that commit's module layout. The volatility probe reads `git log --all`
    instead, which keeps growing with the upstream repository and moves the frozen share between
    runs; bounding it at the last pin puts the gate under the same pinning as the curves.

The baseline is each library's earliest measurable state, which is NOT how the ratchet is
deployed: a real deployment baselines the current state and refuses new backsliding. The
zero-ish baseline inflates the count, and the honest reading is the shape of the series rather
than its total. Chapter 8 says so where it quotes these numbers.

Usage
-----
  python3 experiments/scripts/ratchet_replay.py                  # raw only, from the dumps
  python3 experiments/scripts/ratchet_replay.py --with-gate      # raw + gated, needs clones
  python3 experiments/scripts/ratchet_replay.py --with-gate \
        --clone-root /tmp/coherence-arch-clones

Raw counts need no network: they are read from the committed dumps. The gate needs the
repositories cloned, because suppression is decided on module identity, which the dumps do not
carry. Output lands in `experiments/data/ratchet_replay.json`.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MVP = os.path.abspath(os.path.join(HERE, "..", ".."))
if MVP not in sys.path:
    sys.path.insert(0, MVP)

PINS_PATH = os.path.join(MVP, "experiments", "longitudinal_arch_pins.json")
DATA_DIR = os.path.join(MVP, "experiments", "data")
OUT_PATH = os.path.join(DATA_DIR, "ratchet_replay.json")

LIBS = ["flask", "requests", "httpie", "boltons"]
FROZEN_THRESHOLD = 0.05  # matches probe_volatility_ratchet.py
EPS = 1e-9

SRC = {  # candidate package dirs over history (first existing wins)
    "flask": ["src/flask", "flask"],
    "requests": ["src/requests", "requests"],
    "httpie": ["httpie"],
    "boltons": ["boltons"],
}


# --- raw replay, from the committed dumps -----------------------------------

def raw_replay(lib: str) -> dict:
    """Raw flag count for one library, read from its pinned dump."""
    with open(os.path.join(DATA_DIR, f"longitudinal_arch_{lib}.json")) as fh:
        dump = json.load(fh)

    valid, excluded = [], []
    for point in dump["points"]:
        if "cycle_ratio" in point and "error" not in point:
            valid.append((point["date"], point["sha"], point["cycle_ratio"]))
        else:
            excluded.append({"date": point["date"], "reason": point.get("error", "no_reading")})

    flags, consolidations, intervals = [], [], []
    for i in range(len(valid) - 1):
        (d0, _s0, r0), (d1, _s1, r1) = valid[i], valid[i + 1]
        if r1 > r0 + EPS:
            verdict = "flag"
            flags.append(i)
        elif r1 < r0 - EPS:
            verdict = "consolidation"
            consolidations.append(i)
        else:
            verdict = "hold"
        intervals.append({"interval": f"{d0}->{d1}",
                          "cycle_ratio": f"{r0:.4f}->{r1:.4f}", "verdict": verdict})

    return {
        "library": lib,
        "n_pinned": len(dump["points"]),
        "n_measurable": len(valid),
        "excluded": excluded,
        "n_intervals": len(valid) - 1,
        "raw_flags": len(flags),
        "consolidations": len(consolidations),
        "first_ratio": valid[0][2] if valid else None,
        "last_ratio": valid[-1][2] if valid else None,
        "intervals": intervals,
    }


# --- the frozen-share gate, at the same pinned SHAs --------------------------

def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args],
                          capture_output=True, text=True).stdout.strip()


def srcdir_for(repo: str, lib: str):
    for cand in SRC[lib]:
        path = os.path.join(repo, cand)
        if os.path.isdir(path):
            return path
    return None


def cyclic_modules(root: str):
    """Modules caught in a dependency cycle (SCC > 1), reusing archmetrics' own collectors."""
    from coherence_ratchet import archmetrics as am

    mods = am._collect_modules(root)
    internal = set(mods)
    pkg = os.path.basename(os.path.normpath(root))
    adj = {m: set() for m in internal}
    for mod, path in mods.items():
        adj[mod] |= am._edges_for(path, mod, pkg, internal)
    cyclic = set()
    for comp in am._tarjan(list(internal), adj):
        if len(comp) > 1:
            cyclic |= set(comp)
    n = len(internal)
    return cyclic, n, (len(cyclic) / n if n else 0.0)


def volatility(repo: str, lib: str, last_sha: str):
    """Max-normalised per-module commit frequency, bounded at the last pinned commit.

    `probe_volatility_ratchet.py` reads volatility from `git log --all`, which keeps growing as
    the upstream repository does: the same gate re-run months later reads a different frozen
    share and can suppress a different set of flags. That is the epoch dependency the pinned
    SHAs exist to remove, so this walks only the ancestry of the last pinned commit and reads
    the module layout at that commit. The reading is then fixed by the pins, like every other
    number the replay prints.

    Module attribution reuses probe_hyperliminal.cochange's package-relative suffix matching,
    which survives the historical `requests/` -> `src/requests/` move.
    """
    from collections import defaultdict

    from coherence_ratchet import archmetrics as am

    restore = git(repo, "rev-parse", "HEAD")
    try:
        subprocess.run(["git", "-C", repo, "checkout", "-q", "-f", last_sha],
                       capture_output=True, text=True)
        srcdir = srcdir_for(repo, lib)
        if not srcdir:
            return {}, 0
        mods = am._collect_modules(srcdir)
        parent = os.path.dirname(os.path.normpath(srcdir))
        suffix_to_mod = {os.path.relpath(os.path.abspath(p), parent): m for m, p in mods.items()}

        def match(path):
            if path in suffix_to_mod:
                return suffix_to_mod[path]
            for suf, mod in suffix_to_mod.items():
                if path.endswith("/" + suf):
                    return mod
            return None

        # ancestry of the last pinned commit only -- not --all, and not time-unbounded
        out = subprocess.run(
            ["git", "-C", repo, "log", last_sha, "--no-merges", "--format=__C__%H",
             "--name-only"], capture_output=True, text=True).stdout
    finally:
        subprocess.run(["git", "-C", repo, "checkout", "-q", "-f", restore],
                       capture_output=True, text=True)

    commits, cur = [], None
    for line in out.splitlines():
        if line.startswith("__C__"):
            if cur:
                commits.append(cur)
            cur = set()
        elif line.strip().endswith(".py") and cur is not None:
            mod = match(line.strip())
            if mod:
                cur.add(mod)
    if cur:
        commits.append(cur)

    changes = defaultdict(int)
    for commit in commits:
        for mod in commit:
            changes[mod] += 1
    if not changes:
        return {}, 0
    mx = max(changes.values())
    return {m: c / mx for m, c in changes.items()}, mx


def gated_replay(lib: str, clone_root: str, pins: dict) -> dict:
    """Re-walk the pinned SHAs, recording cyclic module sets, then apply the frozen-share gate."""
    repo = os.path.join(clone_root, lib)
    if not os.path.isdir(os.path.join(repo, ".git")):
        raise SystemExit(f"no clone for {lib} at {repo}; clone {pins[lib]['clone']} first")

    restore = git(repo, "symbolic-ref", "--short", "-q", "HEAD") or git(repo, "rev-parse", "HEAD")
    vol, mx_commits = volatility(repo, lib, pins[lib]["shas"][-1])

    samples = []
    try:
        for sha in pins[lib]["shas"]:
            checkout = subprocess.run(["git", "-C", repo, "checkout", "-q", "-f", sha],
                                      capture_output=True, text=True)
            if checkout.returncode != 0:
                raise SystemExit(f"{lib}: pinned SHA {sha} not present in the clone")
            date = git(repo, "show", "-s", "--format=%cI", sha)[:10]
            srcdir = srcdir_for(repo, lib)
            if not srcdir:
                samples.append({"date": date, "measurable": False})
                continue
            cyc, n, ratio = cyclic_modules(srcdir)
            samples.append({"date": date, "measurable": True,
                            "cyclic": cyc, "n_mods": n, "ratio": ratio})
    finally:
        subprocess.run(["git", "-C", repo, "checkout", "-q", "-f", restore],
                       capture_output=True, text=True)

    usable = [s for s in samples if s["measurable"]]
    raw, gated, suppressed = 0, 0, []
    for i in range(len(usable) - 1):
        a, b = usable[i], usable[i + 1]
        if b["ratio"] <= a["ratio"] + EPS:
            continue
        raw += 1
        newly = b["cyclic"] - a["cyclic"]
        live = [m for m in newly if vol.get(m, 0.0) > FROZEN_THRESHOLD]
        if live:
            gated += 1
            continue
        suppressed.append({
            "interval": f"{a['date']}->{b['date']}",
            "cycle_ratio": f"{a['ratio']:.4f}->{b['ratio']:.4f}",
            "n_mods": f"{a['n_mods']}->{b['n_mods']}",
            "newly_cyclic": sorted((round(vol.get(m, 0.0), 3), m.split(".")[-1]) for m in newly),
            "kind": "denominator-shift" if not newly else "all-frozen",
            "true_positive_suppression": None if not newly else True,
        })

    return {
        "library": lib,
        "n_measurable": len(usable),
        "n_intervals": len(usable) - 1,
        "raw_flags": raw,
        "gated_flags": gated,
        "suppressed": suppressed,
        "frozen_share": round(sum(1 for v in vol.values() if v <= FROZEN_THRESHOLD) / len(vol), 3)
        if vol else 0.0,
        "max_commits_per_module": mx_commits,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--with-gate", action="store_true",
                    help="also compute the frozen-share gate (needs the repositories cloned)")
    ap.add_argument("--clone-root", default="/tmp/coherence-arch-clones")
    ap.add_argument("--libs", nargs="*", default=LIBS)
    args = ap.parse_args()

    with open(PINS_PATH) as fh:
        pins = json.load(fh)

    out = {
        "experiment": "ratchet replay over the pinned architecture-curve commits",
        "rule_raw": "flag interval t->t+1 when cycle_ratio(t+1) > cycle_ratio(t)",
        "rule_gate": ("keep a raw flag only when a module newly entering a cycle has volatility "
                      f"> {FROZEN_THRESHOLD}; otherwise suppress as all-frozen or "
                      "denominator-shift"),
        "sampling": "the 16 pinned commits per library in longitudinal_arch_pins.json",
        "excluded_samples": "commits with no package directory yet; not scored as zero",
        "baseline_caveat": ("baselines at the earliest measurable state, which inflates the count "
                            "against a real deployment that baselines the current state"),
        "frozen_threshold": FROZEN_THRESHOLD,
        "libraries": {},
    }

    for lib in args.libs:
        record = raw_replay(lib)
        if args.with_gate:
            gate = gated_replay(lib, args.clone_root, pins)
            if gate["raw_flags"] != record["raw_flags"]:
                gate["disagrees_with_dump"] = (
                    f"gate walk counted {gate['raw_flags']} raw flags, dump replay counted "
                    f"{record['raw_flags']}")
            record["gate"] = gate
        out["libraries"][lib] = record
        line = (f"{lib:9} intervals={record['n_intervals']:3} "
                f"raw_flags={record['raw_flags']:3} consolidations={record['consolidations']:3}")
        if args.with_gate:
            line += (f" gated={record['gate']['gated_flags']:3} "
                     f"suppressed={len(record['gate']['suppressed']):3}")
        print(line)

    with open(OUT_PATH, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=False)
        fh.write("\n")
    print(f"\nwrote {os.path.relpath(OUT_PATH, MVP)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

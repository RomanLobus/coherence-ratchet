"""Architecture-level decay curves: run archmetrics.measure_arch across a
library's git history and record cycle_ratio, coupling and the Martin
main-sequence signals (mean_abstractness, mean_distance, zone_of_pain_ratio).

Mirror of longitudinal.py one level up: architecture, not function duplication.

Reproducibility contract
------------------------
Even-index sampling over a *growing* history is epoch-dependent: the same code
run six months later samples different commits and prints different digits.
So the sampled commits are pinned. experiments/longitudinal_arch_pins.json is
the source of record for every library: clone URL, source-directory candidates
over history, and the full 40-character SHAs of the sampled commits. Runs read
those SHAs verbatim; they are derived once, per library, and then frozen.

N_SAMPLES stays at 16 for the architecture curves. longitudinal.py (function
duplication) uses 24. Those two numbers are deliberately different and must not
be unified: moving the architecture curves to 24 would change every printed
digit, including httpie's, and forfeit the verification recorded in the pins
file.

The working tree is never mutated. Measurement happens in a detached git
worktree under a temporary directory, and a clone with any uncommitted change is
refused outright rather than checked out over.

Usage
-----
  python3 longitudinal_arch.py --pins                    # all pinned libraries
  python3 longitudinal_arch.py --pins flask requests     # a subset
  python3 longitudinal_arch.py --derive boltons          # derive + write pins
  python3 longitudinal_arch.py --verify                  # exit 1 on any drift
  python3 longitudinal_arch.py --dense flask \
        --from <sha> --to <sha> --dense-n 12             # bracketed re-sample

Per-library output lands in experiments/data/longitudinal_arch_<lib>.json.
longitudinal_arch_out.json is the historical httpie record and is never
rewritten by this script.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from coherence_ratchet.archmetrics import measure_arch  # noqa: E402

PINS_PATH = os.path.join(HERE, "experiments", "longitudinal_arch_pins.json")
DATA_DIR = os.path.join(HERE, "experiments", "data")
DEFAULT_CLONE_ROOT = "/tmp/coherence-arch-clones"

# 16 for the architecture curves; longitudinal.py uses 24 for function
# duplication. See the module docstring before changing either.
N_SAMPLES = 16

# Measurement month, passed as a literal: this tooling runs where date calls are
# unavailable, and a stamped month has to be stable across re-runs anyway.
MEASURED_AT = "2026-08"

SAMPLING = ("even-index over first-parent history, "
            "idx = round(i*(len-1)/(n-1)); pinned by full SHA thereafter")

NUMERIC_FIELDS = ("mods", "edges", "cyclic_modules", "unreadable_modules",
                  "cycle_ratio", "coupling", "instab", "A", "D", "dmods", "pain")


# --------------------------------------------------------------------------- git

def git(repo: str, *args: str) -> str:
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout.strip()


def git_ok(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def is_clean(repo: str) -> bool:
    """True when the clone has no staged, unstaged or untracked change."""
    return git(repo, "status", "--porcelain") == ""


def require_clean(repo: str) -> None:
    if not is_clean(repo):
        raise SystemExit(
            f"refusing to measure {repo}: the clone has uncommitted or untracked\n"
            "changes. This script moves through history and will not risk a working\n"
            "tree that holds unsaved work. Commit, stash or discard, or point\n"
            "--clone-root at a scratch clone."
        )


def history(repo: str) -> list[tuple[str, str]]:
    out = git(repo, "log", "--first-parent", "--format=%H|%cI", "--reverse")
    return [tuple(line.split("|", 1)) for line in out.splitlines() if "|" in line]


def commit_date(repo: str, sha: str) -> str:
    return git(repo, "show", "-s", "--format=%cI", sha)


def ensure_clone(name: str, clone_url: str, clone_root: str) -> str:
    path = os.path.join(clone_root, name)
    if os.path.isdir(os.path.join(path, ".git")):
        return path
    os.makedirs(clone_root, exist_ok=True)
    print(f"cloning {name} from {clone_url} -> {path}")
    r = subprocess.run(["git", "clone", "-q", clone_url, path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"clone of {name} failed: {r.stderr.strip()}")
    return path


# ------------------------------------------------------------------- sampling

def sample_indices(length: int, n: int) -> list[int]:
    if length <= n:
        return list(range(length))
    return [round(i * (length - 1) / (n - 1)) for i in range(n)]


# ------------------------------------------------------------------ analyser

def analyser_fingerprint() -> dict:
    src = os.path.join(HERE, "coherence_ratchet", "archmetrics.py")
    with open(src, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()[:16]
    version = "unknown"
    try:
        with open(os.path.join(HERE, "pyproject.toml"), encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("version"):
                    version = line.split("=", 1)[1].strip().strip('"')
                    break
    except OSError:
        pass
    return {"package": "coherence-ratchet", "version": version,
            "function": "coherence_ratchet.archmetrics.measure_arch",
            "source_sha256_16": digest, "n_samples": N_SAMPLES,
            # The reading is interpreter-dependent wherever a file fails to parse, so the
            # interpreter is part of the provenance, not an environment detail.
            "python": f"{sys.version_info.major}.{sys.version_info.minor}"}


# --------------------------------------------------------------- measurement

def _src_dir(tree: str, candidates: list[str]) -> str | None:
    """First existing candidate wins. This is the package directory, not the
    repo root: repositories move between flat and src/ layouts over their life."""
    for c in candidates:
        p = os.path.join(tree, c)
        if os.path.isdir(p):
            return p
    return None


def strip_type_checking(root: str) -> int:
    """Blank the body of every `if TYPE_CHECKING:` block under root, so
    annotation-only imports stop counting as dependency edges.

    Calibration probe, not the default reading. Python projects put imports
    under TYPE_CHECKING precisely because they are not runtime dependencies, so
    a cycle made only of those edges cannot be a runtime cycle. Whether it is
    still a *knowledge* dependency is the arguable part, which is why both
    variants get recorded rather than one being declared correct. Runs inside
    the throwaway worktree; the next `checkout -f` restores the files.
    """
    touched = 0
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    src = fh.read()
                tree = ast.parse(src)
            except (SyntaxError, OSError):
                continue
            # Replace the whole `if TYPE_CHECKING:` statement with an
            # equally-indented `pass`. Blanking only the body would leave an
            # empty block, and blanking at column zero would break the
            # enclosing indentation — either way the file would stop parsing
            # and `_edges_for` would silently return no edges at all, which
            # looks exactly like a dramatic result. Hence the parse assertion
            # below.
            blank: set[int] = set()
            replace: dict[int, str] = {}
            for node in ast.walk(tree):
                if not isinstance(node, ast.If):
                    continue
                test = node.test
                name = getattr(test, "id", None) or getattr(test, "attr", None)
                if name != "TYPE_CHECKING":
                    continue
                end = node.end_lineno or node.lineno
                replace[node.lineno] = " " * node.col_offset + "pass"
                for ln in range(node.lineno + 1, end + 1):
                    blank.add(ln)
            if not replace:
                continue
            lines = src.splitlines()
            out = []
            for i, ln in enumerate(lines, start=1):
                if i in replace:
                    out.append(replace[i])
                elif i in blank:
                    out.append("")
                else:
                    out.append(ln)
            new_src = "\n".join(out) + "\n"
            try:
                ast.parse(new_src)
            except SyntaxError as exc:
                raise SystemExit(
                    f"TYPE_CHECKING strip broke {path} ({exc}). A stripped file that "
                    "no longer parses contributes zero edges and would fake a result; "
                    "refusing to report the run."
                )
            touched += 1
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new_src)
    return touched


CALIBRATIONS = ("none", "no-type-checking")


def measure_shas(repo: str, shas: list[str], src_candidates: list[str],
                 calibration: str = "none") -> list[dict]:
    """Measure each SHA in a throwaway detached worktree. The primary working
    tree of `repo` is never touched."""
    require_clean(repo)
    wt = tempfile.mkdtemp(prefix="arch-wt-")
    shutil.rmtree(wt)  # git worktree add wants to create the directory itself
    add = git_ok(repo, "worktree", "add", "--detach", "-q", wt, shas[0])
    if add.returncode != 0:
        raise SystemExit(f"could not create worktree for {repo}: {add.stderr.strip()}")
    pts: list[dict] = []
    try:
        for sha in shas:
            co = git_ok(wt, "checkout", "-q", "-f", "--detach", sha)
            date = commit_date(repo, sha)
            rec: dict = {"date": date[:10], "sha": sha}
            if co.returncode != 0:
                rec["error"] = "checkout_failed"
                pts.append(rec)
                continue
            srcdir = _src_dir(wt, src_candidates)
            if not srcdir:
                rec["error"] = "no_src"
                pts.append(rec)
                continue
            if calibration == "no-type-checking":
                rec["tc_files_stripped"] = strip_type_checking(srcdir)
            try:
                s = measure_arch(srcdir).as_dict()
            except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
                rec["error"] = type(exc).__name__
                pts.append(rec)
                continue
            rec.update({"mods": s["n_modules"], "edges": s["n_edges"],
                        # The numerator behind cycle_ratio. A ratio alone cannot tell an
                        # improvement from a growing denominator, and the book's own instrument
                        # argument turns on that distinction, so the dump carries both.
                        "cyclic_modules": s["cyclic_modules"],
                        # Files the parser could not read contribute no edges. Recording the count
                        # is what makes a run comparable across interpreters; see the note in
                        # archmetrics._edges_for.
                        "unreadable_modules": s["unreadable_modules"],
                        "cycle_ratio": s["cycle_ratio"],
                        "coupling": s["coupling_density"], "instab": s["mean_instability"],
                        "A": s["mean_abstractness"], "D": s["mean_distance"],
                        "dmods": s["distance_modules"], "pain": s["zone_of_pain_ratio"]})
            pts.append(rec)
    finally:
        git_ok(repo, "worktree", "remove", "--force", wt)
        shutil.rmtree(wt, ignore_errors=True)
        git_ok(repo, "worktree", "prune")
    return pts


def build_record(name: str, cfg: dict, repo: str, shas: list[str],
                 points: list[dict], calibration: str = "none", **extra) -> dict:
    rec = {
        "library": name,
        "clone": cfg["clone"],
        "src_candidates": cfg["src"],
        "commits_total": cfg.get("commits_total") or len(history(repo)),
        "first": cfg.get("first"),
        "last": cfg.get("last"),
        "n_samples": len(shas),
        "sampling": SAMPLING,
        "calibration": calibration,
        "measured_at": MEASURED_AT,
        "analyser": analyser_fingerprint(),
        "shas": shas,
        "points": points,
    }
    rec.update(extra)
    return rec


# ------------------------------------------------------------------ printing

HEAD = (f"{'date':12}{'mods':>6}{'edges':>7}{'cyc_mods':>9}{'cycle_r':>9}{'coupling':>9}"
        f"{'instab':>8}{'A':>8}{'D':>7}{'dmods':>7}{'pain':>7}")


def print_table(rec: dict) -> None:
    cal = rec.get("calibration", "none")
    print(f"\n### {rec['library']}  ({rec['commits_total']} commits, "
          f"{rec['first']} -> {rec['last']}, n={rec['n_samples']}"
          f"{'' if cal == 'none' else ', calibration=' + cal})")
    print(HEAD)
    for p in rec["points"]:
        if "error" in p:
            print(f"{p['date']:12}{'ERR:' + p['error']:>40}  {p['sha'][:8]}")
        else:
            print(f"{p['date']:12}{p['mods']:>6}{p['edges']:>7}{p.get('cyclic_modules','-'):>9}{p['cycle_ratio']:>9}{p['coupling']:>9}"
                  f"{p['instab']:>8}{p['A']:>8}{p['D']:>7}{p['dmods']:>7}{p['pain']:>7}")


# ----------------------------------------------------------------- pins file

def load_pins() -> dict:
    with open(PINS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def save_pins(pins: dict) -> None:
    with open(PINS_PATH, "w", encoding="utf-8") as fh:
        json.dump(pins, fh, indent=2)
        fh.write("\n")


def libraries(pins: dict) -> list[str]:
    return [k for k in pins if not k.startswith("_")]


def dump_path(name: str, suffix: str = "") -> str:
    return os.path.join(DATA_DIR, f"longitudinal_arch_{name}{suffix}.json")


def write_dump(rec: dict, suffix: str = "") -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    path = dump_path(rec["library"], suffix)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1)
        fh.write("\n")
    return path


# --------------------------------------------------------------------- modes

def run_pinned(names: list[str], clone_root: str, write: bool = True,
               calibration: str = "none") -> dict[str, dict]:
    pins = load_pins()
    out: dict[str, dict] = {}
    for name in names:
        cfg = pins.get(name)
        if cfg is None:
            raise SystemExit(f"{name} has no pins; derive them first "
                             f"(--derive {name})")
        if not cfg.get("shas"):
            raise SystemExit(f"{name} is in the pins file with no SHAs; "
                             f"run --derive {name}")
        repo = ensure_clone(name, cfg["clone"], clone_root)
        points = measure_shas(repo, cfg["shas"], cfg["src"], calibration)
        rec = build_record(name, cfg, repo, cfg["shas"], points,
                           calibration=calibration, mode="pins")
        print_table(rec)
        if write:
            suffix = "" if calibration == "none" else "_no-type-checking"
            print(f"(wrote {write_dump(rec, suffix)})")
        out[name] = rec
    return out


def derive(name: str, clone_url: str, src: list[str], clone_root: str,
           n: int, force: bool) -> dict:
    pins = load_pins()
    existing = pins.get(name)
    if existing and existing.get("shas") and not force:
        raise SystemExit(f"{name} already has pins. Pinned SHAs are the record; "
                         f"pass --force-derive only with a written reason.")
    if existing:
        clone_url = clone_url or existing["clone"]
        src = src or existing["src"]
    if not clone_url or not src:
        raise SystemExit(f"--derive {name} needs --clone URL and --src DIR[,DIR]")
    repo = ensure_clone(name, clone_url, clone_root)
    require_clean(repo)
    hist = history(repo)
    if not hist:
        raise SystemExit(f"{name}: empty first-parent history")
    shas = [hist[k][0] for k in sample_indices(len(hist), n)]
    for sha in shas:
        assert len(sha) == 40, f"short SHA derived: {sha}"
    cfg = {"clone": clone_url, "src": src, "commits_total": len(hist),
           "first": hist[0][1][:10], "last": hist[-1][1][:10], "shas": shas}
    pins[name] = cfg
    save_pins(pins)
    print(f"derived {len(shas)} pins for {name} "
          f"({cfg['commits_total']} commits, {cfg['first']} -> {cfg['last']})")
    return cfg


def dense(name: str, sha_from: str, sha_to: str, n: int, clone_root: str,
          calibration: str = "none", write: bool = True) -> dict:
    """Re-sample densely between two bracketing commits, to separate a genuine
    step change from a sampling artefact."""
    pins = load_pins()
    cfg = pins[name]
    repo = ensure_clone(name, cfg["clone"], clone_root)
    require_clean(repo)
    hist = history(repo)
    order = {sha: i for i, (sha, _d) in enumerate(hist)}
    for s in (sha_from, sha_to):
        if s not in order:
            raise SystemExit(f"{s} is not on {name}'s first-parent history")
    lo, hi = sorted((order[sha_from], order[sha_to]))
    window = hist[lo:hi + 1]
    shas = [window[k][0] for k in sample_indices(len(window), n)]
    points = measure_shas(repo, shas, cfg["src"], calibration)
    rec = build_record(name, cfg, repo, shas, points,
                       calibration=calibration, mode="dense",
                       window={"from": sha_from, "to": sha_to,
                               "first_parent_commits_in_window": len(window),
                               "from_date": window[0][1][:10],
                               "to_date": window[-1][1][:10]})
    rec["first"] = window[0][1][:10]
    rec["last"] = window[-1][1][:10]
    print_table(rec)
    # the window goes in the filename, so one dense window never overwrites another
    suffix = f"_dense_{rec['first']}_{rec['last']}"
    if calibration != "none":
        suffix += "_" + calibration
    if write:
        print(f"(wrote {write_dump(rec, suffix)})")
    return rec


def verify(names: list[str], clone_root: str) -> int:
    """Re-measure at the pinned SHAs and compare to the committed dumps.
    Any numeric difference is a failure: the pins exist so these digits stay put."""
    pins = load_pins()
    failures = 0
    for name, suffix in [(n, s) for n in names for s in ("", "_no-type-checking")]:
        path = dump_path(name, suffix)
        if suffix and not os.path.exists(path):
            continue  # calibration dumps are optional
        if not os.path.exists(path):
            print(f"FAIL[{name}]: no committed dump at {path}")
            failures += 1
            continue
        with open(path, encoding="utf-8") as fh:
            want = json.load(fh)
        # A parse failure is interpreter-dependent, and a file that fails to parse contributes no
        # edges, so the same pinned commit can read differently under a different Python. Say so
        # before printing a wall of drift that looks like the analyser broke.
        stamped = (want.get("analyser") or {}).get("python")
        running = f"{sys.version_info.major}.{sys.version_info.minor}"
        if stamped and stamped != running:
            print(f"  note[{name}{suffix}]: dump measured on Python {stamped}, running {running}; "
                  "any drift below may be a parse difference rather than an analyser change")

        cfg = pins[name]
        if want.get("shas") != cfg.get("shas"):
            print(f"FAIL[{name}{suffix}]: dump SHAs differ from the pins file")
            failures += 1
            continue
        repo = ensure_clone(name, cfg["clone"], clone_root)
        got = measure_shas(repo, cfg["shas"], cfg["src"],
                           want.get("calibration", "none"))
        diffs = compare_points(want["points"], got)
        if diffs:
            failures += 1
            print(f"FAIL[{name}{suffix}]: {len(diffs)} numeric difference(s)")
            for d in diffs[:20]:
                print(f"  {d}")
        else:
            print(f"ok[{name}{suffix}]: {len(got)}/{len(got)} points reproduce "
                  f"({', '.join(NUMERIC_FIELDS)})")
    return failures


def compare_points(want: list[dict], got: list[dict]) -> list[str]:
    diffs: list[str] = []
    if len(want) != len(got):
        return [f"point count {len(got)} != recorded {len(want)}"]
    for w, g in zip(want, got):
        if w["sha"] != g["sha"]:
            diffs.append(f"{w['sha'][:8]}: sha mismatch, measured {g['sha'][:8]}")
            continue
        if ("error" in w) != ("error" in g):
            diffs.append(f"{w['sha'][:8]}: error state changed "
                         f"({w.get('error')} -> {g.get('error')})")
            continue
        for f in NUMERIC_FIELDS:
            if f in w and w[f] != g.get(f):
                diffs.append(f"{w['sha'][:8]} {w['date']} {f}: "
                             f"recorded {w[f]}, measured {g.get(f)}")
    return diffs


# ---------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pins", nargs="*", metavar="LIB",
                    help="measure at the committed SHAs (default: every pinned library)")
    ap.add_argument("--verify", nargs="*", metavar="LIB",
                    help="re-measure at the pinned SHAs and exit 1 on any numeric drift")
    ap.add_argument("--derive", metavar="LIB",
                    help="derive fresh pins for a library and write them to the pins file")
    ap.add_argument("--clone", metavar="URL", default="", help="clone URL, for --derive")
    ap.add_argument("--src", metavar="DIR[,DIR]", default="",
                    help="source-dir candidates over history, for --derive (first existing wins)")
    ap.add_argument("--force-derive", action="store_true",
                    help="overwrite existing pins (changes every printed digit)")
    ap.add_argument("--dense", metavar="LIB", help="dense re-sample inside a window")
    ap.add_argument("--from", dest="sha_from", metavar="SHA", help="window start, for --dense")
    ap.add_argument("--to", dest="sha_to", metavar="SHA", help="window end, for --dense")
    ap.add_argument("--dense-n", type=int, default=12, help="samples inside the window")
    ap.add_argument("--n-samples", type=int, default=N_SAMPLES,
                    help=f"samples for --derive (default {N_SAMPLES}; see the docstring)")
    ap.add_argument("--clone-root", default=DEFAULT_CLONE_ROOT,
                    help=f"where clones live, one directory per library (default {DEFAULT_CLONE_ROOT})")
    ap.add_argument("--calibration", choices=CALIBRATIONS, default="none",
                    help="'no-type-checking' re-reads the graph with `if TYPE_CHECKING:` "
                         "imports excluded, as a sensitivity check on the cycle ratio")
    ap.add_argument("--no-write", action="store_true", help="print only, write no dump")
    args = ap.parse_args(argv)

    if args.derive:
        src = [s for s in args.src.split(",") if s]
        derive(args.derive, args.clone, src, args.clone_root,
               args.n_samples, args.force_derive)
        return 0

    if args.dense:
        if not (args.sha_from and args.sha_to):
            raise SystemExit("--dense needs --from SHA and --to SHA")
        dense(args.dense, args.sha_from, args.sha_to, args.dense_n, args.clone_root,
              args.calibration, write=not args.no_write)
        return 0

    if args.verify is not None:
        names = args.verify or libraries(load_pins())
        failures = verify(names, args.clone_root)
        if failures:
            print(f"\nevidence check FAILED: {failures} library/libraries drifted")
            return 1
        print(f"\nevidence check passed: {len(names)} library/libraries reproduce")
        return 0

    names = args.pins if args.pins else libraries(load_pins())
    run_pinned(names, args.clone_root, write=not args.no_write,
               calibration=args.calibration)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""D2 probe — single-use dependency sprawl on real libraries.

SIG (Software Improvement Group, 2026 — vendor) names "libraries introduced for a single
use and never cleaned up" as part of the AI drift signature. The detector
(`coherence_ratchet.signals.dependency_sprawl`) counts third-party (non-stdlib,
non-internal) top-level imports and flags the ones used in exactly ONE module of the
package. This probe runs it on flask / requests / httpie (mature, deliberately
small-footprint libraries — the honest expectation is a LOW yield here; the signal
targets AI-era application code, where dependencies accrete per-task) and, cheaply from
git history, samples the distinct third-party import count over time.

History sampling uses `git grep` at sampled first-parent commits (regex on import lines,
so it tolerates the Python-2-era files that `ast` cannot parse).
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from coherence_ratchet.signals import _STDLIB, dependency_sprawl

GH = "/private/tmp/claude-503/-Users-roman-lobus-Projects-sdd/aecc079f-06e5-4505-9684-81264219f95f/scratchpad/gh-test"
TARGETS = {
    # name: (repo dir, source subdir today, historical pathspecs to try — the source tree
    # moved over time (requests/ -> src/requests/; earliest flask was a single flask.py))
    "flask": ("flask", "src/flask",
              [":(glob)src/flask/**/*.py", ":(glob)flask/**/*.py", "flask.py"]),
    "requests": ("requests", "src/requests",
                 [":(glob)src/requests/**/*.py", ":(glob)requests/**/*.py", "requests.py"]),
    "httpie": ("httpie", "httpie", [":(glob)httpie/**/*.py"]),
}

_IMPORT = re.compile(r"^\s*(?:import\s+([A-Za-z_][\w.]*)|from\s+([A-Za-z_][\w.]*)\s+import)")


def _git(repo, *args):
    return subprocess.run(["git", "-C", repo] + list(args),
                          capture_output=True, text=True).stdout


def history_thirdparty(repo, pkg, prefixes, samples=6):
    """(iso_date, n_thirdparty) at evenly sampled first-parent commits, oldest first."""
    shas = _git(repo, "rev-list", "--first-parent", "HEAD").split()
    if not shas:
        return []
    shas = shas[::-1]                     # oldest -> newest
    idx = sorted({round(i * (len(shas) - 1) / (samples - 1)) for i in range(samples)})
    out = []
    for i in idx:
        sha = shas[i]
        date = _git(repo, "show", "-s", "--format=%as", sha).strip()
        deps = set()
        for pathspec in prefixes:
            # POSIX ERE: git grep has no \s, use [[:space:]]
            text = _git(repo, "grep", "-h", "-E", "^[[:space:]]*(import|from)[[:space:]]",
                        sha, "--", pathspec)
            for line in text.splitlines():
                m = _IMPORT.match(line.strip())
                if not m:
                    continue
                top = (m.group(1) or m.group(2)).split(".")[0]
                if top and top != pkg and top not in _STDLIB:
                    deps.add(top)
            if text:
                break                     # the pathspec that exists at this commit
        out.append((date, len(deps)))
    return out


def main():
    for name, (sub, src, prefixes) in TARGETS.items():
        repo = os.path.join(GH, sub)
        root = os.path.join(repo, src)
        if not os.path.isdir(root):
            print(f"{name}: {src} missing — skipped")
            continue
        single, total, rows = dependency_sprawl(root)
        n_modules = len({m for r in rows for m in r["modules"]})
        print(f"\n### {name} — {total} distinct third-party imports, "
              f"{single} single-use")
        for r in rows:
            tag = "SINGLE-USE" if r["n_modules"] == 1 else f"{r['n_modules']} modules"
            mods = ", ".join(m.split(".")[-1] for m in r["modules"][:4])
            more = "…" if r["n_modules"] > 4 else ""
            print(f"  {r['dependency']:<22} {tag:<12} ({mods}{more})")
        hist = history_thirdparty(repo, name, prefixes)
        if hist:
            print("  dependency-count churn (first-parent samples, oldest -> newest):")
            print("    " + "   ".join(f"{d}:{n}" for d, n in hist))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""The coherence signal portfolio — the deterministic floor, packaged.

One place to compute every deterministic signal the book's method watches, so the CLI and the
ratchet can read them together (the P4/P8 lesson: no single metric is enough). All signals here
are deterministic and stdlib-only. The LLM semantic pass and the behaviour-complete proof are the
layers above this floor; they are NOT here.

Signals:
  - function-level duplication (via metrics.measure)
  - architecture: dependency cycles, coupling, fan-in (via archmetrics.measure_arch)
  - connascence of meaning: significant literals shared across >= 2 modules
  - (optional, needs a git repo) hyperliminal coupling + contagion (via the change history)

`measure_all(root, repo=None)` returns a Composite whose `.to_dict()` carries every signal, so a
Budget can ratchet the portfolio. Coupling is reported but NOT ratcheted (healthy consolidation
raises it) — see ratchet.WATCHED.
"""
from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from itertools import combinations

from . import archmetrics as am
from .metrics import Snapshot, measure, _iter_py_files, _module_name

# --- connascence of meaning -------------------------------------------------

_TRIVIAL_NUMS = {0, 1, 2, -1, 10, 100, 1000, 0.0, 1.0, 0.5}


def _significant(v) -> bool:
    if isinstance(v, bool):
        return False
    if isinstance(v, str):
        return len(v) >= 4 and not v.isspace()
    if isinstance(v, (int, float)):
        return v not in _TRIVIAL_NUMS and abs(v) > 2
    return False


def connascence_of_meaning(root: str):
    """Significant literals shared across >= 2 modules — implicit agreements that break silently.
    Returns (count, rows) where count is the number of such shared literals."""
    lit: dict = {}
    for path in _iter_py_files(root):
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        mod = _module_name(root, path)
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and _significant(n.value):
                lit.setdefault((type(n.value).__name__, n.value), set()).add(mod)
    rows = [
        {"value": repr(v)[:50], "modules": sorted(mods)}
        for (t, v), mods in lit.items()
        if len(mods) >= 2
    ]
    rows.sort(key=lambda r: len(r["modules"]), reverse=True)
    return len(rows), rows


# --- hyperliminal coupling (optional; needs git history) --------------------

def hyperliminal(repo: str, root: str, jaccard_min: float = 0.25, min_co: int = 3):
    """Modules that co-change but share no static import edge — the hidden coupling the graph
    misses — plus contagion (mean commit blast radius). Returns (hyper_count, contagion_mean, rows).
    Deferred import of the probe helpers keeps the core dependency-free when no repo is given."""
    import subprocess
    from collections import defaultdict

    mods = am._collect_modules(root)
    internal = set(mods)
    pkg = os.path.basename(os.path.normpath(root))
    static_edges = set()
    for m, p in mods.items():
        for t in am._edges_for(p, m, pkg, internal):
            if t != m:
                static_edges.add(frozenset((m, t)))
    parent = os.path.dirname(os.path.normpath(root))
    suffix_to_mod = {os.path.relpath(p, parent): m for m, p in mods.items()}

    def match(path):
        if path in suffix_to_mod:
            return suffix_to_mod[path]
        for suf, m in suffix_to_mod.items():
            if path.endswith("/" + suf):
                return m
        return None

    out = subprocess.run(
        ["git", "-C", repo, "log", "--all", "-n4000", "--no-merges", "--format=__C__%H", "--name-only"],
        capture_output=True, text=True).stdout
    commits, cur = [], None
    for line in out.splitlines():
        if line.startswith("__C__"):
            if cur is not None:
                commits.append(cur)
            cur = set()
        elif line.strip().endswith(".py") and cur is not None:
            m = match(line.strip())
            if m:
                cur.add(m)
    if cur is not None:
        commits.append(cur)
    commits = [c for c in commits if c]
    if not commits:
        return 0, 0.0, []
    changes, pair = defaultdict(int), defaultdict(int)
    blast = []
    for c in commits:
        blast.append(len(c))
        for m in c:
            changes[m] += 1
        for a, b in combinations(sorted(c), 2):
            pair[frozenset((a, b))] += 1
    rows = []
    for fs, co in pair.items():
        a, b = tuple(fs)
        union = changes[a] + changes[b] - co
        j = co / union if union else 0.0
        if co >= min_co and j >= jaccard_min and fs not in static_edges:
            rows.append({"pair": [a.split(".")[-1], b.split(".")[-1]], "jaccard": round(j, 3), "co": co})
    rows.sort(key=lambda r: r["jaccard"], reverse=True)
    return len(rows), round(sum(blast) / len(blast), 2), rows


# --- composite --------------------------------------------------------------

@dataclass
class Composite:
    snapshot: Snapshot
    arch: dict
    connascence_shared: int
    hyperliminal_pairs: int = 0
    contagion_mean: float = 0.0
    detail: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = self.snapshot.to_dict()
        d.update({
            "n_modules": self.arch["n_modules"],
            "cycle_ratio": self.arch["cycle_ratio"],
            "coupling_density": self.arch["coupling_density"],
            "max_fan_in_ratio": self.arch["max_fan_in_ratio"],
            "connascence_shared": self.connascence_shared,
            "hyperliminal_pairs": self.hyperliminal_pairs,
            "contagion_mean": self.contagion_mean,
        })
        return d


def measure_all(root: str, repo: str | None = None) -> Composite:
    snap = measure(root)
    arch = am.measure_arch(root).as_dict()
    conn_count, conn_rows = connascence_of_meaning(root)
    hp, cont, hrows = (0, 0.0, [])
    if repo:
        try:
            hp, cont, hrows = hyperliminal(repo, root)
        except Exception:
            hp, cont, hrows = (0, 0.0, [])
    return Composite(
        snapshot=snap, arch=arch, connascence_shared=conn_count,
        hyperliminal_pairs=hp, contagion_mean=cont,
        detail={"connascence": conn_rows[:10], "hyperliminal": hrows[:10]},
    )

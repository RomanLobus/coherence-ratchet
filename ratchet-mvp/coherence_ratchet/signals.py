"""The coherence signal portfolio — the deterministic floor, packaged.

One place to compute every deterministic signal the book's method watches, so the CLI and the
ratchet can read them together (the P4/P8 lesson: no single metric is enough). All signals here
are deterministic and stdlib-only. Semantic candidate surfacing and behavioural evidence are
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
import sys
from dataclasses import dataclass, field
from itertools import combinations

from . import archmetrics as am
from .metrics import Snapshot, measure, _iter_py_files, _module_name
from .paths import resolve_root

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


# --- dependency sprawl (third-party import spread) ---------------------------

# stdlib top-level names; Python 3.10+. `__future__` is included by CPython.
#
# This was `getattr(sys, "stdlib_module_names", ())` while the package claimed to support 3.9. On
# 3.9 the attribute is absent, so the fallback made `_STDLIB` empty and every `import os` counted as
# a third-party dependency: the dependency-sprawl signal inverted, silently, and a 3.9 reader got a
# different number from the one printed in the book. The package now requires 3.10, and a missing
# attribute is a real error rather than a wrong reading.
_STDLIB = frozenset(sys.stdlib_module_names)


def _is_type_checking(test) -> bool:
    return (isinstance(test, ast.Name) and test.id == "TYPE_CHECKING") or (
        isinstance(test, ast.Attribute) and test.attr == "TYPE_CHECKING")


def _runtime_nodes(tree):
    """walk the AST skipping `if TYPE_CHECKING:` bodies — stub-only imports are not
    runtime dependencies."""
    stack = list(ast.iter_child_nodes(tree))
    while stack:
        n = stack.pop()
        if isinstance(n, ast.If) and _is_type_checking(n.test):
            stack.extend(n.orelse)
            continue
        yield n
        stack.extend(ast.iter_child_nodes(n))


def dependency_sprawl(root: str):
    """Third-party import spread: which non-stdlib, non-internal top-level packages the tree
    imports at runtime, and how many of its modules use each. The single-use ones — a
    dependency imported in exactly one module — are the SIG (2026) AI-drift signature:
    'libraries introduced for a single use and never cleaned up'. Informational signal,
    never ratcheted (a single-use dependency can be a perfectly deliberate adapter).

    Returns (single_use_count, total_third_party, rows); rows carry each dependency with the
    modules that import it, single-use first. TYPE_CHECKING-only imports are excluded."""
    pkg = os.path.basename(os.path.normpath(root))
    users: dict[str, set[str]] = {}
    for path in _iter_py_files(root):
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        mod = _module_name(root, path) or "__init__"
        for n in _runtime_nodes(tree):
            tops = []
            if isinstance(n, ast.Import):
                tops = [a.name.split(".")[0] for a in n.names]
            elif isinstance(n, ast.ImportFrom) and not n.level and n.module:
                tops = [n.module.split(".")[0]]
            for top in tops:
                if top and top != pkg and top not in _STDLIB:
                    users.setdefault(top, set()).add(mod)
    rows = [
        {"dependency": dep, "n_modules": len(mods), "modules": sorted(mods)}
        for dep, mods in users.items()
    ]
    rows.sort(key=lambda r: (r["n_modules"], r["dependency"]))
    single = sum(1 for r in rows if r["n_modules"] == 1)
    return single, len(rows), rows


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

    # capture_output does not raise on a failed git, it returns empty stdout, and an empty log is
    # indistinguishable from a repository whose modules never co-change. A path that is not a
    # repository, or a missing git, would otherwise be reported as a clean history.
    proc = subprocess.run(
        ["git", "-C", repo, "log", "--all", "-n4000", "--no-merges", "--format=__C__%H", "--name-only"],
        capture_output=True, text=True)
    if proc.returncode != 0:
        detail = (proc.stderr or "").strip().splitlines()
        raise RuntimeError(
            f"git log failed in {repo}: {detail[0] if detail else 'exit ' + str(proc.returncode)}")
    out = proc.stdout
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
    # dependency sprawl (informational, never ratcheted — see dependency_sprawl)
    third_party_imports: int = 0
    single_use_third_party: int = 0
    # Set when the change-history read failed, so a zero can be told from an unmeasured signal.
    # Deliberately kept out of to_dict(): the budgets file and the ratchet compare measurements,
    # and an error string is not one.
    history_error: str | None = None
    detail: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = self.snapshot.to_dict()
        d.update({
            "n_modules": self.arch["n_modules"],
            "cycle_ratio": self.arch["cycle_ratio"],
            "coupling_density": self.arch["coupling_density"],
            "max_fan_in_ratio": self.arch["max_fan_in_ratio"],
            # Raw numerators for every ratio above. Density metrics mislead under volume
            # inflation (Larsen & Moghaddam, SEAA 2026: agentic-AI adoption left smell counts
            # flat while LOC grew ~13%, so every density "improved"); raw counts and explicit
            # decomposition are required alongside each ratio.
            "cyclic_modules": self.arch["cyclic_modules"],
            "n_edges": self.arch["n_edges"],
            "max_fan_in": self.arch["max_fan_in"],
            "connascence_shared": self.connascence_shared,
            "hyperliminal_pairs": self.hyperliminal_pairs,
            "contagion_mean": self.contagion_mean,
            "third_party_imports": self.third_party_imports,
            "single_use_third_party": self.single_use_third_party,
        })
        return d


def measure_all(root: str, repo: str | None = None, *,
                sim_threshold: float | None = None) -> Composite:
    resolve_root(root)
    snap = measure(root, sim_threshold=sim_threshold)
    arch = am.measure_arch(root).as_dict()
    conn_count, conn_rows = connascence_of_meaning(root)
    single_use, third_party, dep_rows = dependency_sprawl(root)
    hp, cont, hrows = (0, 0.0, [])
    history_error = None
    if repo:
        try:
            hp, cont, hrows = hyperliminal(repo, root)
        except Exception as exc:
            # Zero co-changing pairs is a real and good reading; a missing git binary, a path that
            # is not a repository, or a failed match is not that reading. Returning them as the same
            # number reported a clean history the tool never measured, which is the inverse of the
            # rule the semantic layer follows, where a failed judge is reported as a failure.
            history_error = str(exc) or exc.__class__.__name__
            hp, cont, hrows = (0, 0.0, [])
    return Composite(
        snapshot=snap, arch=arch, connascence_shared=conn_count,
        hyperliminal_pairs=hp, contagion_mean=cont,
        third_party_imports=third_party, single_use_third_party=single_use,
        history_error=history_error,
        detail={"connascence": conn_rows[:10], "hyperliminal": hrows[:10],
                "dependencies": dep_rows[:10]},
    )

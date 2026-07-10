"""Architecture-level coherence metrics — the module-dependency analogue of the
function-level divergence detector.

Builds the intra-package module dependency graph from imports and reports the
classic architectural-decay signals: dependency cycles (violations of the
acyclic-dependencies principle), coupling density, fan-in concentration
("god modules"), and instability. Dependency-free, stdlib only.
"""
from __future__ import annotations

import ast
import os
from dataclasses import dataclass, asdict


@dataclass
class ArchSnapshot:
    n_modules: int
    n_edges: int
    coupling_density: float       # internal import edges per module
    cycle_count: int              # number of dependency cycles (SCCs of size > 1)
    cyclic_modules: int           # modules caught in some cycle
    cycle_ratio: float            # cyclic_modules / n_modules  (headline decay signal)
    largest_cycle: int            # size of the largest SCC
    max_fan_in: int               # most depended-upon module (god-module signal)
    max_fan_in_ratio: float       # max_fan_in / n_modules
    mean_instability: float       # mean Ce/(Ca+Ce)
    # Martin's main-sequence signals (A-I-D). Abstractness is approximated for Python
    # as the share of a module's classes that are ABCs/Protocols/@abstractmethod-bearing.
    mean_abstractness: float      # mean A over modules that declare >=1 class
    mean_distance: float          # mean D = |A + I - 1| over modules with both A and I defined
    distance_modules: int         # how many modules contributed to mean_distance
    zone_of_pain: int             # modules that are concrete AND stable (A<0.3, I<0.3) — brittle, hard to change
    zone_of_pain_ratio: float     # zone_of_pain / distance_modules

    def as_dict(self):
        d = asdict(self)
        for k in ("coupling_density", "cycle_ratio", "max_fan_in_ratio", "mean_instability",
                  "mean_abstractness", "mean_distance", "zone_of_pain_ratio"):
            d[k] = round(d[k], 4)
        return d


def _module_name(pkg_name: str, rel: str) -> str:
    parts = rel[:-3].split(os.sep)  # strip .py
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join([pkg_name] + parts) if parts else pkg_name


def _collect_modules(root: str) -> dict[str, str]:
    """map dotted module name -> file path, for every .py under root."""
    pkg = os.path.basename(os.path.normpath(root))
    mods = {}
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if fn.endswith(".py"):
                rel = os.path.relpath(os.path.join(dirpath, fn), root)
                mods[_module_name(pkg, rel)] = os.path.join(dirpath, fn)
    return mods


def _resolve(name: str, internal: set[str]) -> str | None:
    """longest internal module that `name` refers to (module or its package)."""
    if name in internal:
        return name
    # an imported symbol may be `pkg.mod.symbol`; back off to the module
    parts = name.split(".")
    for i in range(len(parts), 0, -1):
        cand = ".".join(parts[:i])
        if cand in internal:
            return cand
    return None


def _edges_for(path: str, mod: str, pkg: str, internal: set[str]) -> set[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError, OSError):
        return set()
    base = mod.rsplit(".", 1)[0] if "." in mod else mod  # the module's package
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                t = _resolve(a.name, internal)
                if t and t != mod:
                    out.add(t)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:           # relative import
                up = base.split(".")
                up = up[: len(up) - (node.level - 1)] if node.level > 1 else up
                target = ".".join(up + ([node.module] if node.module else []))
            else:                                        # absolute
                target = node.module or ""
            if not target.startswith(pkg):
                # could still be a relative-resolved internal; check anyway
                pass
            t = _resolve(target, internal)
            if t and t != mod:
                out.add(t)
            # also consider `from pkg.mod import submod` where submod is a module
            for a in node.names:
                t2 = _resolve((target + "." + a.name) if target else a.name, internal)
                if t2 and t2 != mod:
                    out.add(t2)
    return out


def _attr_name(node) -> str:
    """dotted name for an ast.Name / ast.Attribute (e.g. abc.ABC -> 'abc.ABC')."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _attr_name(node.value) + "." + node.attr
    return ""


def _is_abstract_class(node: ast.ClassDef) -> bool:
    """Python analogue of 'abstract class or interface': inherits ABC/Protocol,
    uses an ABCMeta metaclass, or declares an @abstractmethod."""
    for b in node.bases:
        n = _attr_name(b)
        if n.split(".")[-1] in ("ABC", "Protocol"):
            return True
    for kw in node.keywords:
        if kw.arg == "metaclass" and _attr_name(kw.value).split(".")[-1] == "ABCMeta":
            return True
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in item.decorator_list:
                if "abstractmethod" in _attr_name(d) or "abstractproperty" in _attr_name(d):
                    return True
    return False


def _abstractness(path: str):
    """(n_classes, n_abstract) for a module file; (0, 0) if unparseable or class-free."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
    except (SyntaxError, UnicodeDecodeError, OSError):
        return 0, 0
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    n_abstract = sum(1 for c in classes if _is_abstract_class(c))
    return len(classes), n_abstract


def _tarjan(nodes: list[str], adj: dict[str, set[str]]) -> list[list[str]]:
    index = {}
    low = {}
    on = set()
    stack = []
    sccs = []
    counter = [0]
    import sys
    sys.setrecursionlimit(10000)

    def strong(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on.add(v)
        for w in adj.get(v, ()):  # only internal edges present
            if w not in index:
                strong(w)
                low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on.discard(w)
                comp.append(w)
                if w == v:
                    break
            sccs.append(comp)

    for v in nodes:
        if v not in index:
            strong(v)
    return sccs


def measure_arch(root: str) -> ArchSnapshot:
    mods = _collect_modules(root)
    internal = set(mods)
    pkg = os.path.basename(os.path.normpath(root))
    adj: dict[str, set[str]] = {m: set() for m in internal}
    for mod, path in mods.items():
        adj[mod] |= _edges_for(path, mod, pkg, internal)
    n = len(internal)
    n_edges = sum(len(v) for v in adj.values())
    # fan-in / fan-out
    fan_out = {m: len(adj[m]) for m in internal}
    fan_in = {m: 0 for m in internal}
    for m in internal:
        for t in adj[m]:
            fan_in[t] += 1
    sccs = _tarjan(list(internal), adj)
    cyc = [c for c in sccs if len(c) > 1]
    cyclic_modules = sum(len(c) for c in cyc)
    largest = max((len(c) for c in cyc), default=0)
    instability = {}
    for m in internal:
        ce, ca = fan_out[m], fan_in[m]
        if ce + ca > 0:
            instability[m] = ce / (ce + ca)
    instabilities = list(instability.values())
    # abstractness per module, and distance from the main sequence where both A and I exist
    abstractness = {}
    for m, path in mods.items():
        nc, na = _abstractness(path)
        if nc > 0:
            abstractness[m] = na / nc
    distances = []
    pain = 0
    for m in internal:
        if m in abstractness and m in instability:
            a, i = abstractness[m], instability[m]
            distances.append(abs(a + i - 1))
            if a < 0.3 and i < 0.3:        # concrete and stable -> zone of pain (brittle)
                pain += 1
    max_fi = max(fan_in.values(), default=0)
    return ArchSnapshot(
        n_modules=n,
        n_edges=n_edges,
        coupling_density=(n_edges / n) if n else 0.0,
        cycle_count=len(cyc),
        cyclic_modules=cyclic_modules,
        cycle_ratio=(cyclic_modules / n) if n else 0.0,
        largest_cycle=largest,
        max_fan_in=max_fi,
        max_fan_in_ratio=(max_fi / n) if n else 0.0,
        mean_instability=(sum(instabilities) / len(instabilities)) if instabilities else 0.0,
        mean_abstractness=(sum(abstractness.values()) / len(abstractness)) if abstractness else 0.0,
        mean_distance=(sum(distances) / len(distances)) if distances else 0.0,
        distance_modules=len(distances),
        zone_of_pain=pain,
        zone_of_pain_ratio=(pain / len(distances)) if distances else 0.0,
    )


if __name__ == "__main__":
    import sys, json
    print(json.dumps(measure_arch(sys.argv[1]).as_dict(), indent=1))

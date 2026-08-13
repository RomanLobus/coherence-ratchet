"""Deterministic coherence metrics for the coherence ratchet MVP.

No LLM. Given a Python source tree, measure two proxies for design coherence:

  - redundancy: clusters of near-duplicate functions — the same idea
    implemented more than once in slightly different ways. This is the
    decay an additive AI author produces: a fourth retry helper that
    nobody noticed already existed three times.

  - coupling: how tangled the module import graph is (fan-out per module,
    total internal edges).

Both are computed from the AST, so the result is exact and reproducible —
the property the LLM coherence gate cannot offer and the MVP deliberately
does not depend on.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field, asdict
from typing import Iterable

from .paths import SourceTreeError, resolve_root  # noqa: F401  (re-exported for callers)


# --- function fingerprinting ------------------------------------------------

# Functions shorter than this many structural tokens are ignored. Tiny
# functions (getters, __init__, one-liners) collide by accident and tell us
# nothing about design redundancy.
MIN_TOKENS = 12

# k for k-gram shingling of the token stream.
SHINGLE_K = 5

# Jaccard similarity at or above this counts two functions as "the same idea,
# implemented again". Calibrated against the playground fixture, where genuine
# re-implementations of the same helper score 0.43-1.0 pairwise while unrelated
# functions stay below 0.20 — a wide gap. 0.45 sits inside it: the whole retry
# family clusters (directly or transitively) and nothing unrelated does. A real
# codebase needs its own calibration, and the divergent copies that slip under
# any structural threshold are exactly what the (out-of-MVP) semantic gate adds.
SIM_THRESHOLD = 0.45


def _func_tokens(fn: ast.AST) -> list[str]:
    """A structure-preserving token stream for one function.

    Local names are normalised away (so renaming does not hide a copy), but
    call targets, attribute names and constant *types* are kept (so genuinely
    different logic stays distinct). This is a Type-2/Type-3 clone signature.
    """
    toks: list[str] = []

    def visit(n: ast.AST) -> None:
        if isinstance(n, ast.Call):
            toks.append("CALL")
            func = n.func
            if isinstance(func, ast.Name):
                toks.append("CALLEE_" + func.id)
                for a in n.args:
                    visit(a)
                for kw in n.keywords:
                    visit(kw)
                return
            if isinstance(func, ast.Attribute):
                toks.append("CALLEE_" + func.attr)
                visit(func.value)
                for a in n.args:
                    visit(a)
                for kw in n.keywords:
                    visit(kw)
                return
        if isinstance(n, ast.Attribute):
            toks.append("ATTR_" + n.attr)
        elif isinstance(n, ast.Name):
            toks.append("NAME")
        elif isinstance(n, ast.arg):
            toks.append("ARG")
        elif isinstance(n, ast.Constant):
            toks.append("CONST_" + type(n.value).__name__)
        else:
            toks.append(type(n).__name__)
        for c in ast.iter_child_nodes(n):
            visit(c)

    for stmt in fn.body:
        visit(stmt)
    return toks


def _shingles(tokens: list[str], k: int = SHINGLE_K) -> set[str]:
    if len(tokens) < k:
        return {"".join(tokens)} if tokens else set()
    return {"".join(tokens[i : i + k]) for i in range(len(tokens) - k + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    if inter == 0:
        return 0.0
    return inter / len(a | b)


# --- union-find -------------------------------------------------------------

class _UF:
    def __init__(self, n: int) -> None:
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[ra] = rb


# --- data shapes ------------------------------------------------------------

@dataclass
class FunctionRecord:
    qualname: str
    tokens: list[str] = field(repr=False)
    shingles: set[str] = field(repr=False)


@dataclass
class Snapshot:
    total_functions: int
    redundant_functions: int
    redundant_clusters: int
    duplication_ratio: float
    total_internal_edges: int
    max_module_fanout: int
    clusters: list[list[str]]  # member qualnames per redundancy cluster

    def to_dict(self) -> dict:
        d = asdict(self)
        d["duplication_ratio"] = round(self.duplication_ratio, 4)
        return d


# --- scanning ---------------------------------------------------------------

def _iter_py_files(root: str) -> Iterable[str]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", ".git"}]
        for fn in sorted(filenames):
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


def _module_name(root: str, path: str) -> str:
    rel = os.path.relpath(path, root)
    rel = rel[:-3] if rel.endswith(".py") else rel
    parts = [p for p in rel.split(os.sep) if p != "__init__"]
    return ".".join(parts)


def _collect_functions(root: str) -> list[FunctionRecord]:
    records: list[FunctionRecord] = []
    for path in _iter_py_files(root):
        try:
            with open(path, encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        mod = _module_name(root, path)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Dunder methods implement language protocols (__eq__, __getstate__,
                # …); their similarity is mandated by the protocol, not a design
                # choice, so counting them as redundancy is noise.
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue
                toks = _func_tokens(node)
                if len(toks) < MIN_TOKENS:
                    continue
                records.append(
                    FunctionRecord(
                        qualname=f"{mod}.{node.name}",
                        tokens=toks,
                        shingles=_shingles(toks),
                    )
                )
    return records


def _coupling(root: str) -> tuple[int, int]:
    """Module-level internal import edges and the worst single-module fan-out.

    A diagnostic, not a ratchet metric: raw coupling is not purely
    lower-is-better, because consolidating duplicates deliberately raises
    (healthy) coupling to the shared helper. Ratcheting bad coupling needs an
    allowed-dependency spec (boundary violations), which is out of MVP scope.
    """
    modules: set[str] = {_module_name(root, p) for p in _iter_py_files(root)}
    fanout: dict[str, set[str]] = {}
    total = 0
    for path in _iter_py_files(root):
        mod = _module_name(root, path)
        try:
            with open(path, encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        targets: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    targets.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                targets.add(node.module)
        internal = {t for t in targets if t in modules and t != mod}
        fanout[mod] = internal
        total += len(internal)
    max_fanout = max((len(v) for v in fanout.values()), default=0)
    return total, max_fanout


def measure(root: str, *, sim_threshold: float | None = None) -> Snapshot:
    resolve_root(root)
    # The default is the shipped constant, so every existing call site and every fixture the book
    # prints reads exactly as before. A reader who has run `calibrate` passes their own value.
    threshold = SIM_THRESHOLD if sim_threshold is None else sim_threshold
    funcs = _collect_functions(root)
    n = len(funcs)
    uf = _UF(n)
    # O(n^2) pairwise — fine for the playground; an MVP, not a scaler.
    for i in range(n):
        si = funcs[i].shingles
        for j in range(i + 1, n):
            if _jaccard(si, funcs[j].shingles) >= threshold:
                uf.union(i, j)
    groups: dict[int, list[int]] = {}
    for i in range(n):
        groups.setdefault(uf.find(i), []).append(i)
    clusters = [
        sorted(funcs[i].qualname for i in members)
        for members in groups.values()
        if len(members) >= 2
    ]
    clusters.sort()
    redundant_functions = sum(len(c) for c in clusters)
    total_edges, max_fanout = _coupling(root)
    return Snapshot(
        total_functions=n,
        redundant_functions=redundant_functions,
        redundant_clusters=len(clusters),
        duplication_ratio=(redundant_functions / n) if n else 0.0,
        total_internal_edges=total_edges,
        max_module_fanout=max_fanout,
        clusters=clusters,
    )

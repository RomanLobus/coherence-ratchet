"""P3 — connascence as a fragmentation signal (Page-Jones; Fundamentals Ch.3, BEA Ch.5).

The book's signals (duplication, cycles, coupling, fan-in) catch connascence of
*algorithm* (same idea reimplemented) and *name* (imports). They are blind to
**connascence of meaning**: the same magic value / convention hard-coded in several
modules, an implicit agreement that breaks when one site changes and the others do
not. Connascence theory also says coupling should be ranked by strength x locality x
degree, and that distant connascence is worse than local — a principled way to
*prioritise* what to consolidate that a raw count does not give.

Two parts:
  (A) connascence-of-meaning detector — significant literals shared across >= 2
      modules, ranked by module-spread (locality) x occurrences (degree). NEW signal.
  (B) reinterpret the existing duplicate clusters as connascence of algorithm and
      weight them by locality (same-file < same-package < cross-package) x degree,
      to show ranking differs from raw cluster size.
"""
import os
import ast, os, sys, math
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from coherence_ratchet.metrics import (
    _iter_py_files, _module_name, _func_tokens, _shingles, _jaccard, _UF,
    SIM_THRESHOLD, MIN_TOKENS,
)

# literals too common to be a meaningful shared agreement
TRIVIAL_NUMS = {0, 1, 2, -1, 10, 100, 1000, 0.0, 1.0, 0.5}
def _significant(v):
    if isinstance(v, bool):
        return False
    if isinstance(v, str):
        return len(v) >= 4 and not v.isspace()
    if isinstance(v, int) or isinstance(v, float):
        return v not in TRIVIAL_NUMS and abs(v) > 2
    return False

def connascence_of_meaning(root):
    # literal value -> {module: count}
    lit = defaultdict(lambda: defaultdict(int))
    for path in _iter_py_files(root):
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        mod = _module_name(root, path)
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and _significant(n.value):
                lit[(type(n.value).__name__, n.value)][mod] += 1
    rows = []
    for (typ, val), mods in lit.items():
        if len(mods) >= 2:  # shared across modules = cross-module connascence of meaning
            occ = sum(mods.values())
            rows.append({"value": repr(val)[:50], "type": typ, "modules": len(mods),
                         "occurrences": occ, "where": sorted(mods)[:4]})
    # rank by locality (module spread) then degree (occurrences)
    rows.sort(key=lambda r: (r["modules"], r["occurrences"]), reverse=True)
    return rows

# locality weight: how far apart the connascent elements sit
def _pkg(mod):  # top package of a dotted module name
    return mod.split(".")[0] if "." in mod else mod
def locality_weight(mods):
    files = set(mods); pkgs = {_pkg(m) for m in mods}
    if len(files) == 1: return 1   # same module — local, cheap
    if len(pkgs) == 1:  return 2   # same package
    return 3                       # cross-package — worst

def algorithm_clusters(root):
    recs = []
    for path in _iter_py_files(root):
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        mod = _module_name(root, path)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue
                toks = _func_tokens(node)
                if len(toks) >= MIN_TOKENS:
                    recs.append((f"{mod}.{node.name}", mod, _shingles(toks)))
    n = len(recs); uf = _UF(n)
    for i in range(n):
        for j in range(i+1, n):
            if _jaccard(recs[i][2], recs[j][2]) >= SIM_THRESHOLD:
                uf.union(i, j)
    groups = defaultdict(list)
    for i in range(n): groups[uf.find(i)].append(i)
    clusters = []
    for members in groups.values():
        if len(members) < 2: continue
        mods = [recs[i][1] for i in members]
        deg = len(members)
        loc = locality_weight(mods)
        # connascence-of-algorithm harm: strong static form, weighted by locality x degree
        score = loc * deg
        clusters.append({"degree": deg, "locality": loc, "score": score,
                         "names": [recs[i][0].split(".")[-1] for i in members][:6]})
    return clusters

def main(name, root):
    print(f"\n===== {name} =====")
    com = connascence_of_meaning(root)
    print(f"[A] connascence of meaning — {len(com)} literals shared across >=2 modules (top 12 by spread):")
    print(f"{'mods':>5}{'occ':>5}  {'type':<6} value                         where")
    for r in com[:12]:
        print(f"{r['modules']:>5}{r['occurrences']:>5}  {r['type']:<6} {r['value']:<28} {', '.join(w.split('.')[-1] for w in r['where'])}")
    clusters = algorithm_clusters(root)
    by_score = sorted(clusters, key=lambda c: c["score"], reverse=True)
    by_size  = sorted(clusters, key=lambda c: c["degree"], reverse=True)
    print(f"\n[B] connascence of algorithm — {len(clusters)} clusters. Ranking differs from raw size:")
    print(f"  top-3 by raw degree:   " + " | ".join(f"deg{c['degree']}loc{c['locality']}({','.join(c['names'][:2])})" for c in by_size[:3]))
    print(f"  top-3 by conn. score:  " + " | ".join(f"score{c['score']}=loc{c['locality']}xdeg{c['degree']}({','.join(c['names'][:2])})" for c in by_score[:3]))
    crossp = [c for c in clusters if c["locality"] == 3]
    print(f"  {len(crossp)}/{len(clusters)} clusters are cross-package (locality 3 — worst, prioritise); "
          f"{sum(1 for c in clusters if c['locality']==1)} are same-module (local, cheap)")

if __name__ == "__main__":
    GH = os.environ.get("CR_CORPUS", "/tmp/gh-test")
    targets = {"requests": "src/requests", "flask": "src/flask", "httpie": "httpie", "sqlalchemy": "lib/sqlalchemy"}
    which = sys.argv[1] if len(sys.argv) > 1 else None
    for nm, sub in targets.items():
        if which and nm != which: continue
        root = os.path.join(GH, nm, sub)
        if os.path.isdir(root): main(nm, root)
        else: print(f"{nm}: {sub} missing")

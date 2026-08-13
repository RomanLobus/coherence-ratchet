"""P2 — SRP / Common-Closure change-driver guard.

The duplication detector says "these N functions are the same idea — consolidate."
But Common Closure (Martin, Clean Arch Ch.13) says only consolidate code that
*changes together*. Two look-alike functions that change for different reasons must
stay separate; merging them creates a false shared dependency that explodes on
divergence — a CCP violation the behaviour-complete proof cannot see (the proof only
checks the merge preserves *current* behaviour, not future coupling).

This probe computes, for each multi-file duplicate cluster, the git co-change of the
files holding its members (Jaccard of their commit sets over full history). Question:
does co-change separate "safe to consolidate" (high — they evolve together) from
"leave divergent" (≈0 — different change drivers)?
"""
import subprocess, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from coherence_ratchet.metrics import (
    _iter_py_files, _module_name, _func_tokens, _shingles, _jaccard,
    _UF, SIM_THRESHOLD, MIN_TOKENS,
)
import ast

def collect(root):
    """[(qualname, relpath, shingles)] for every non-dunder function >= MIN_TOKENS."""
    recs = []
    for path in _iter_py_files(root):
        try:
            with open(path, encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        mod = _module_name(root, path)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue
                toks = _func_tokens(node)
                if len(toks) < MIN_TOKENS:
                    continue
                recs.append((f"{mod}.{node.name}", path, _shingles(toks)))
    return recs

def cluster(recs):
    n = len(recs)
    uf = _UF(n)
    for i in range(n):
        for j in range(i+1, n):
            if _jaccard(recs[i][2], recs[j][2]) >= SIM_THRESHOLD:
                uf.union(i, j)
    groups = {}
    for i in range(n):
        groups.setdefault(uf.find(i), []).append(i)
    return [m for m in groups.values() if len(m) >= 2]

def commit_set(repo, relpath):
    out = subprocess.run(["git","-C",repo,"log","--follow","--format=%H","--",relpath],
                         capture_output=True, text=True).stdout
    return set(out.split())

def main(repo, srcsub):
    root = os.path.join(repo, srcsub)
    recs = collect(root)
    clusters = cluster(recs)
    # cache commit sets per file
    cache = {}
    def cs(p):
        rel = os.path.relpath(p, repo)
        if rel not in cache:
            cache[rel] = commit_set(repo, rel)
        return cache[rel]

    rows = []
    for members in clusters:
        files = sorted({recs[i][1] for i in members})
        if len(files) < 2:
            continue  # single-file cluster: same change driver by construction
        # pairwise co-change Jaccard over commit sets
        pair_scores = []
        for a in range(len(files)):
            for b in range(a+1, len(files)):
                sa, sb = cs(files[a]), cs(files[b])
                if sa or sb:
                    inter = len(sa & sb)
                    union = len(sa | sb)
                    pair_scores.append(inter/union if union else 0.0)
        if not pair_scores:
            continue
        names = sorted(recs[i][0] for i in members)
        rows.append({
            "members": names,
            "n_files": len(files),
            "cochange_max": round(max(pair_scores), 3),
            "cochange_mean": round(sum(pair_scores)/len(pair_scores), 3),
            "files": [os.path.relpath(f, repo) for f in files],
        })
    rows.sort(key=lambda r: r["cochange_max"])
    print(f"\n##### {os.path.basename(repo)} — {len(recs)} funcs, "
          f"{len(clusters)} dup clusters, {len(rows)} span >=2 files")
    print(f"{'cochg_max':>10}{'cochg_mean':>11}{'files':>6}   members")
    for r in rows:
        print(f"{r['cochange_max']:>10}{r['cochange_mean']:>11}{r['n_files']:>6}   "
              + ", ".join(m.split('.')[-1] for m in r['members'])
              + "   [" + " | ".join(r['files']) + "]")
    lo = [r for r in rows if r["cochange_max"] == 0.0]
    hi = [r for r in rows if r["cochange_max"] >= 0.2]
    print(f"\nsummary: {len(lo)}/{len(rows)} cross-file clusters NEVER co-changed "
          f"(different change drivers -> leave); {len(hi)}/{len(rows)} co-change >=0.2 "
          f"(evolve together -> safe to consolidate)")

if __name__ == "__main__":
    GH = "/private/tmp/claude-503/-Users-roman-lobus-Projects-sdd/aecc079f-06e5-4505-9684-81264219f95f/scratchpad/gh-test"
    targets = {"requests": "src/requests", "flask": "src/flask", "httpie": "httpie"}
    which = sys.argv[1] if len(sys.argv) > 1 else None
    for name, sub in targets.items():
        if which and name != which:
            continue
        repo = os.path.join(GH, name)
        if os.path.isdir(os.path.join(repo, sub)):
            main(repo, sub)
        else:
            print(f"{name}: {sub} missing")

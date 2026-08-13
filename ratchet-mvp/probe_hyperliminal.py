"""RES1 — hyperliminal coupling as a first-party signal.

Residuality Theory (O'Reilly 2024): coupling that is invisible until a change hits — two
components affected by the same stressor are coupled, but the link is not in the dependency
graph. In the incidence matrix (stressors x components), it shows up as two 1s in a row.

Operationalisation for a real codebase, deterministically:
  - "stressor" = a historical change (a commit that touches the source package)
  - a module is "affected" by that stressor if the commit touched it
  - HYPERLIMINAL COUPLING = a pair of modules that CO-CHANGE (share commits) but have NO
    static import edge between them — hidden coupling the dependency graph cannot see.
  - CONTAGION = commit blast radius (how many modules a single change touches).

This is co-change (probe_cochange) intersected with the static graph (archmetrics): the part
of empirical change-coupling that the import graph misses. It targets the book's "beyond-context"
cost (reframe-E/Eb) with a computable number.
"""
import subprocess, sys, os
from itertools import combinations
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from coherence_ratchet import archmetrics as am

def static_graph(root):
    """undirected set of {frozenset(a,b)} internal import edges, + module->abspath map."""
    mods = am._collect_modules(root)            # dotted -> abspath
    internal = set(mods)
    pkg = os.path.basename(os.path.normpath(root))
    edges = set()
    for mod, path in mods.items():
        for t in am._edges_for(path, mod, pkg, internal):
            if t != mod:
                edges.add(frozenset((mod, t)))
    abspath_to_mod = {os.path.abspath(p): m for m, p in mods.items()}
    return internal, edges, abspath_to_mod

def cochange(repo, root, abspath_to_mod, max_commits=4000):
    """per-module change count, pairwise co-change counts, contagion (commit blast radii).

    Robust to detached/unborn HEAD (uses --all) and to the historical requests/ -> src/requests/
    move (maps a changed path to a module by package-relative suffix)."""
    parent = os.path.dirname(os.path.normpath(root))          # e.g. .../requests/src  (parent of the package dir)
    suffix_to_mod = {}                                        # "requests/models.py" -> "requests.models"
    for ab, m in abspath_to_mod.items():
        suffix_to_mod[os.path.relpath(ab, parent)] = m
    def match(path):
        if path in suffix_to_mod:
            return suffix_to_mod[path]
        for suf, m in suffix_to_mod.items():
            if path.endswith("/" + suf):
                return m
        return None
    out = subprocess.run(
        ["git", "-C", repo, "log", "--all", f"-n{max_commits}", "--no-merges",
         "--format=__C__%H", "--name-only"],
        capture_output=True, text=True).stdout
    commits = []
    cur = None
    for line in out.splitlines():
        if line.startswith("__C__"):
            if cur is not None: commits.append(cur)
            cur = set()
        elif line.strip() and cur is not None and line.strip().endswith(".py"):
            m = match(line.strip())
            if m: cur.add(m)
    if cur is not None: commits.append(cur)
    commits = [c for c in commits if c]                       # commits touching >=1 internal module
    changes = defaultdict(int)
    pair = defaultdict(int)
    blast = []
    for c in commits:
        blast.append(len(c))
        for m in c: changes[m] += 1
        for a, b in combinations(sorted(c), 2):
            pair[frozenset((a, b))] += 1
    return changes, pair, blast, len(commits)

def analyse(name, repo, srcsub, jaccard_min=0.25, min_co=3):
    root = os.path.join(repo, srcsub)
    internal, static_edges, abs2mod = static_graph(root)
    changes, pair, blast, n_commits = cochange(repo, root, abs2mod)
    rows = []
    for fs, co in pair.items():
        a, b = tuple(fs)
        union = changes[a] + changes[b] - co
        j = co / union if union else 0.0
        if co >= min_co and j >= jaccard_min:
            rows.append((round(j, 3), co, fs in static_edges, a.split(".")[-1], b.split(".")[-1]))
    rows.sort(reverse=True)
    if not blast:
        print(f"\n### {name}: no source commits mapped (check clone state)"); return {"hyper":0,"linked":0,"n":len(internal)}
    hyper = [r for r in rows if not r[2]]     # co-change high, NO static edge
    linked = [r for r in rows if r[2]]        # co-change high, static edge present (visible)
    print(f"\n### {name} — {len(internal)} modules, {n_commits} source commits, "
          f"{len(static_edges)} static edges")
    print(f"  contagion (commit blast radius): mean {sum(blast)/len(blast):.2f}, "
          f"max {max(blast)}, commits touching >5 modules: {sum(1 for b in blast if b>5)}")
    print(f"  co-change pairs >= J{jaccard_min}/co{min_co}: {len(rows)}  "
          f"| static-linked {len(linked)}  | HYPERLIMINAL (no static edge) {len(hyper)}")
    print("  top hyperliminal (hidden) couplings:")
    for j, co, _, a, b in hyper[:8]:
        print(f"    J={j:<5} co={co:<3}  {a}  <->  {b}   [no import edge]")
    return {"hyper": len(hyper), "linked": len(linked), "n": len(internal)}

if __name__ == "__main__":
    GH = "/private/tmp/claude-503/-Users-roman-lobus-Projects-sdd/aecc079f-06e5-4505-9684-81264219f95f/scratchpad/gh-test"
    targets = {"requests": "src/requests", "flask": "src/flask", "httpie": "httpie"}
    which = sys.argv[1] if len(sys.argv) > 1 else None
    for nm, sub in targets.items():
        if which and nm != which: continue
        repo = os.path.join(GH, nm)
        if os.path.isdir(os.path.join(repo, sub)):
            analyse(nm, repo, sub)
        else:
            print(f"{nm}: {sub} missing")

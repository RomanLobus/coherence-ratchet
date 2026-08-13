"""RES4 — stress-response consolidation heuristic.

Residuality: components with the SAME stress response (identical incidence-matrix rows) "live and die
together" and can be combined to reduce N. Operationalised: modules whose *change response* is near
identical — very high co-change (Jaccard -> 1) — are module-merge candidates. This is a consolidation
signal distinct from code-duplication (P1), connascence (P3), and even cluster-level co-change (P2 was
function clusters): it flags modules that ALWAYS change together, whether or not they share code.

Question: does stress-response similarity surface consolidation candidates the code-similarity signals
miss, and does it agree with the static graph or reveal hidden module-families?
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import probe_hyperliminal as ph

def analyse(name, repo, srcsub, combine_j=0.5, min_co=3):
    root = os.path.join(repo, srcsub)
    internal, static_edges, abs2mod = ph.static_graph(root)
    changes, pair, blast, n = ph.cochange(repo, root, abs2mod)
    cands = []
    for fs, co in pair.items():
        a, b = tuple(fs)
        union = changes[a] + changes[b] - co
        j = co / union if union else 0.0
        if co >= min_co and j >= combine_j:
            cands.append((round(j, 3), co, fs in static_edges, a.split(".")[-1], b.split(".")[-1]))
    cands.sort(reverse=True)
    linked = sum(1 for c in cands if c[2])
    print(f"\n### {name} — combine-candidates (co-change J>={combine_j}, co>={min_co}): {len(cands)}"
          f"  ({linked} already import-linked, {len(cands)-linked} NOT linked)")
    for j, co, edge, a, b in cands[:10]:
        tag = "linked" if edge else "NO edge (hidden family)"
        print(f"    J={j:<5} co={co:<3}  {a} + {b}   [{tag}]")

if __name__ == "__main__":
    GH = "/private/tmp/claude-503/-Users-roman-lobus-Projects-sdd/aecc079f-06e5-4505-9684-81264219f95f/scratchpad/gh-test"
    for nm, sub in {"requests": "src/requests", "flask": "src/flask", "httpie": "httpie", "sqlalchemy": "lib/sqlalchemy"}.items():
        repo = os.path.join(GH, nm)
        if os.path.isdir(os.path.join(repo, sub)):
            analyse(nm, repo, sub)

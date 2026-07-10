"""P9 — combined consolidation-priority score (connascence x co-change).

P3 (connascence) gives the *structural* "would have to change together" — locality x degree.
P2 (co-change) gives the *empirical* "does change together" — Jaccard of commit sets.
Each alone is flawed: connascence-alone is dominated by degree (ranks intentional symmetry
high); co-change-alone gives no priority magnitude and is ambiguous (low can mean "different
drivers" OR "just stable"). This fuses them: priority = locality x degree x co-change, and
tests whether the product ranks the genuine accidental copy top while demoting deliberate
symmetry, beating either signal alone.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from probe_cochange import collect, cluster, commit_set
from probe_connascence import locality_weight

def analyse(name, repo, srcsub):
    root = os.path.join(repo, srcsub)
    recs = collect(root)                      # (qualname, path, shingles)
    clusters = cluster(recs)
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
            continue
        mods = [recs[i][0].rsplit(".", 1)[0] for i in members]
        degree = len(members)
        locality = locality_weight(mods)
        # co-change: max pairwise Jaccard over the cluster's files
        pair = []
        for a in range(len(files)):
            for b in range(a + 1, len(files)):
                sa, sb = cs(files[a]), cs(files[b])
                if sa or sb:
                    pair.append(len(sa & sb) / len(sa | sb) if (sa | sb) else 0.0)
        cochange = max(pair) if pair else 0.0
        rows.append({
            "name": ", ".join(sorted({recs[i][0].split(".")[-1] for i in members}))[:38],
            "degree": degree, "locality": locality,
            "connascence": locality * degree,            # P3 structural score
            "cochange": round(cochange, 3),              # P2 empirical
            "combined": round(locality * degree * cochange, 2),
        })
    if not rows:
        print(f"\n### {name}: no cross-file clusters"); return
    print(f"\n### {name} — {len(rows)} cross-file clusters")
    def show(key, label):
        top = sorted(rows, key=lambda r: r[key], reverse=True)[:3]
        print(f"  top-3 by {label:18}: " + " | ".join(f"{r['name'][:22]}({r[key]})" for r in top))
    show("connascence", "connascence-alone")
    show("cochange", "cochange-alone")
    show("combined", "COMBINED")

if __name__ == "__main__":
    GH = os.environ.get("CR_CORPUS", "/tmp/gh-test")
    for nm, sub in {"requests": "src/requests", "flask": "src/flask", "httpie": "httpie"}.items():
        repo = os.path.join(GH, nm)
        if os.path.isdir(os.path.join(repo, sub)):
            analyse(nm, repo, sub)

"""P5 — Modularity Maturity Index (Lilienthal; Software Architecture Metrics Ch.4).

MMI is a validated composite of three dimensions: modularity (45%), hierarchy (30%),
pattern consistency (25%). The book already measures modularity-ish signals (coupling,
fan-in) and a hierarchy signal (cycle_ratio). This probe asks three things:
  1. Does an MMI-style composite *discriminate* the four libraries sensibly?
  2. Do the hierarchy and pattern-consistency dimensions add signal *beyond* cycle_ratio?
  3. Does the composite *corroborate* flask's known architectural decay over time?

Honest scope: modularity and hierarchy are computable from the dependency graph;
**pattern consistency is only approximated** (coefficient of variation of module
instability/fan-out) — true pattern consistency needs the catalogue/LLM gate, which is
exactly the book's point. Sub-scores are rough-calibrated (same posture as archmetrics).
"""
import os, sys, statistics
sys.path.insert(0, os.path.dirname(__file__))
from coherence_ratchet import archmetrics as am

def _graph(root):
    mods = am._collect_modules(root)
    internal = set(mods)
    pkg = os.path.basename(os.path.normpath(root))
    adj = {m: set() for m in internal}
    for mod, path in mods.items():
        adj[mod] |= am._edges_for(path, mod, pkg, internal)
    fan_out = {m: len(adj[m]) for m in internal}
    fan_in = {m: 0 for m in internal}
    for m in internal:
        for t in adj[m]:
            fan_in[t] += 1
    return internal, adj, fan_in, fan_out

def _clamp(x): return max(0.0, min(1.0, x))

def mmi(root):
    s = am.measure_arch(root)
    internal, adj, fan_in, fan_out = _graph(root)
    n = max(s.n_modules, 1)
    # --- modularity (45%): low coupling density + no god-module concentration
    mod = _clamp(1 - s.coupling_density / 5.0) * 0.6 + _clamp(1 - s.max_fan_in_ratio) * 0.4
    # --- hierarchy (30%): acyclic + shallow tangles
    hier = _clamp(1 - s.cycle_ratio) * 0.7 + _clamp(1 - s.largest_cycle / n) * 0.3
    # --- pattern consistency (25%): structural uniformity across modules (PROXY)
    insts = []
    for m in internal:
        ce, ca = fan_out[m], fan_in[m]
        if ce + ca > 0:
            insts.append(ce / (ce + ca))
    cv = (statistics.pstdev(insts) / (statistics.mean(insts) + 1e-9)) if len(insts) > 1 else 0.0
    cons = _clamp(1 - cv)
    score = 10 * (0.45 * mod + 0.30 * hier + 0.25 * cons)
    tier = ("critical" if score < 4 else "high" if score < 6 else
            "moderate" if score < 7.5 else "low")
    return {"mmi": round(score, 2), "tier": tier, "mod": round(mod, 3),
            "hier": round(hier, 3), "cons": round(cons, 3),
            "cycle_ratio": s.cycle_ratio, "coupling": s.coupling_density}

GH = "/private/tmp/claude-503/-Users-roman-lobus-Projects-sdd/aecc079f-06e5-4505-9684-81264219f95f/scratchpad/gh-test"
LIBS = {"requests": "src/requests", "flask": "src/flask", "httpie": "httpie", "boltons": "boltons"}

def current_state():
    print(f"{'repo':10}{'MMI':>6}{'tier':>10}{'mod':>7}{'hier':>7}{'cons':>7}{'cycle_r':>9}{'coupl':>7}")
    rows = []
    for name, sub in LIBS.items():
        root = os.path.join(GH, name, sub)
        if not os.path.isdir(root):
            print(f"{name:10} (missing)"); continue
        r = mmi(root); rows.append((name, r))
        print(f"{name:10}{r['mmi']:>6}{r['tier']:>10}{r['mod']:>7}{r['hier']:>7}{r['cons']:>7}{r['cycle_ratio']:>9}{r['coupling']:>7}")
    # does cons (pattern-consistency proxy) add discrimination beyond cycle_ratio?
    print("\nrank by cycle_ratio (asc, healthy first): " +
          " > ".join(n for n,_ in sorted(rows, key=lambda x: x[1]['cycle_ratio'])))
    print("rank by MMI (desc, healthy first):         " +
          " > ".join(n for n,_ in sorted(rows, key=lambda x: -x[1]['mmi'])))
    print("rank by cons proxy (desc):                 " +
          " > ".join(n for n,_ in sorted(rows, key=lambda x: -x[1]['cons'])))

def flask_history():
    import longitudinal_arch as la
    repo = os.path.join(GH, "flask")
    hist = la.history(repo)
    cur = la.git(repo, "symbolic-ref", "--short", "-q", "HEAD") or la.git(repo, "rev-parse", "HEAD")
    import subprocess
    print(f"\nflask MMI trajectory ({len(hist)} commits):")
    print(f"{'date':12}{'MMI':>6}{'tier':>10}{'mod':>7}{'hier':>7}{'cons':>7}{'cycle_r':>9}")
    for k in la.sample(hist, 10):
        sha, date = hist[k]
        subprocess.run(["git","-C",repo,"checkout","-q","-f",sha], capture_output=True, text=True)
        root = next((os.path.join(repo, c) for c in ["src/flask","flask"] if os.path.isdir(os.path.join(repo, c))), None)
        if not root:
            print(f"{date[:10]:12}  no_src"); continue
        try:
            r = mmi(root)
            print(f"{date[:10]:12}{r['mmi']:>6}{r['tier']:>10}{r['mod']:>7}{r['hier']:>7}{r['cons']:>7}{r['cycle_ratio']:>9}")
        except Exception as e:
            print(f"{date[:10]:12}  ERR {type(e).__name__}")
    subprocess.run(["git","-C",repo,"checkout","-q","-f",cur], capture_output=True, text=True)

if __name__ == "__main__":
    current_state()
    if "--hist" in sys.argv:
        flask_history()

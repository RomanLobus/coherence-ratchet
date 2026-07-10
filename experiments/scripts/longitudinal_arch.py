"""Run the architecture-level metrics (archmetrics.measure_arch) across a repo's
git history. Produces decay curves for cycle_ratio, coupling, and the Martin
main-sequence signals (mean_abstractness, mean_distance, zone_of_pain_ratio).

Mirror of longitudinal.py, one level up (architecture, not function duplication).
Tests P1: does the distance-from-main-sequence D decay over time the way
cycle_ratio does, or is it orthogonal / flat?"""
import subprocess, sys, json, os
import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from coherence_ratchet.archmetrics import measure_arch

REPOS = {
 "requests": "/tmp/gh-test/requests",
 "flask":    "/tmp/gh-test/flask",
 "httpie":   "/tmp/gh-test/httpie",
 "boltons":  "/tmp/gh-test/boltons",
}
N_SAMPLES = 16
SRC = {  # library source dir candidates over history (first existing wins); package dir, not src root
 "requests":["src/requests","requests"], "flask":["src/flask","flask"],
 "httpie":["httpie"], "boltons":["boltons"],
}

def git(repo, *args):
    return subprocess.run(["git","-C",repo,*args], capture_output=True, text=True).stdout.strip()

def history(repo):
    out = git(repo,"log","--first-parent","--format=%H|%cI","--reverse")
    return [tuple(l.split("|")) for l in out.splitlines() if "|" in l]

def sample(seq, n):
    if len(seq)<=n: return list(range(len(seq)))
    return [round(i*(len(seq)-1)/(n-1)) for i in range(n)]

def run_repo(name, repo):
    hist=history(repo)
    cur=git(repo,"symbolic-ref","--short","-q","HEAD") or git(repo,"rev-parse","HEAD")
    idxs=sample(hist,N_SAMPLES)
    pts=[]
    for k in idxs:
        sha,date=hist[k]
        subprocess.run(["git","-C",repo,"checkout","-q","-f",sha],capture_output=True,text=True)
        srcdir=next((os.path.join(repo,c) for c in SRC[name] if os.path.isdir(os.path.join(repo,c))), None)
        if not srcdir:
            pts.append({"date":date[:10],"sha":sha[:8],"error":"no_src"}); continue
        try:
            s=measure_arch(srcdir).as_dict()
            pts.append({"date":date[:10],"sha":sha[:8],"mods":s["n_modules"],
                        "cycle_ratio":s["cycle_ratio"],"coupling":s["coupling_density"],
                        "instab":s["mean_instability"],"A":s["mean_abstractness"],
                        "D":s["mean_distance"],"dmods":s["distance_modules"],
                        "pain":s["zone_of_pain_ratio"]})
        except Exception as e:
            pts.append({"date":date[:10],"sha":sha[:8],"error":type(e).__name__})
    subprocess.run(["git","-C",repo,"checkout","-q","-f",cur],capture_output=True,text=True)
    return {"repo":name,"commits_total":len(hist),"first":hist[0][1][:10],"last":hist[-1][1][:10],"points":pts}

if __name__=="__main__":
    which=sys.argv[1] if len(sys.argv)>1 else None
    out={}
    for name,repo in REPOS.items():
        if which and name!=which: continue
        if not os.path.isdir(repo):
            print(f"### {name}: repo clone missing at {repo}"); continue
        out[name]=run_repo(name,repo)
        r=out[name]
        print(f"\n### {name}  ({r['commits_total']} commits, {r['first']} -> {r['last']})")
        print(f"{'date':12}{'mods':>6}{'cycle_r':>9}{'coupling':>9}{'instab':>8}{'A':>7}{'D':>7}{'dmods':>7}{'pain':>7}")
        for p in r["points"]:
            if "error" in p: print(f"{p['date']:12}{'ERR:'+p['error']:>40}")
            else: print(f"{p['date']:12}{p['mods']:>6}{p['cycle_ratio']:>9}{p['coupling']:>9}{p['instab']:>8}{p['A']:>7}{p['D']:>7}{p['dmods']:>7}{p['pain']:>7}")
    json.dump(out, open(os.path.join(os.path.dirname(__file__),"longitudinal_arch_out.json"),"w"), indent=1)
    print("\n(wrote longitudinal_arch_out.json)")

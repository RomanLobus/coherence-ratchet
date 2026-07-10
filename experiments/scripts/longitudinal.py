"""Run the coherence_ratchet divergence metric across a repo's git history.
Produces a decay curve (duplication_ratio over time) + size context, per repo."""
import subprocess, sys, json, os
import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from coherence_ratchet.metrics import measure

REPOS = {
 "requests": "/tmp/gh-test/requests",
 "flask":    "/tmp/gh-test/flask",
 "httpie":   "/tmp/gh-test/httpie",
 "boltons":  "/tmp/gh-test/boltons",
}
N_SAMPLES = 24
SRC = {  # library source dir candidates over history (excludes tests); first existing wins
 "requests":["src/requests","requests"], "flask":["src/flask","flask"],
 "httpie":["httpie"], "boltons":["boltons"],
}

def git(repo, *args):
    return subprocess.run(["git","-C",repo,*args], capture_output=True, text=True).stdout.strip()

def history(repo):
    out = git(repo,"log","--first-parent","--format=%H|%cI","--reverse")
    rows=[l.split("|") for l in out.splitlines() if "|" in l]
    return [(sha,date) for sha,date in rows]

def ai_trailers(repo):
    out = git(repo,"log","--format=%b")
    low=out.lower()
    return {
      "claude": low.count("co-authored-by: claude")+low.count("noreply@anthropic"),
      "copilot": low.count("copilot"),
      "cursor": low.count("cursor"),
    }

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
            s=measure(srcdir)
            pts.append({"date":date[:10],"sha":sha[:8],"n":s.total_functions,
                        "redundant":s.redundant_functions,"clusters":s.redundant_clusters,
                        "dup_ratio":round(s.duplication_ratio,4)})
        except Exception as e:
            pts.append({"date":date[:10],"sha":sha[:8],"error":type(e).__name__})
    subprocess.run(["git","-C",repo,"checkout","-q","-f",cur],capture_output=True,text=True)
    return {"repo":name,"commits_total":len(hist),"first":hist[0][1][:10],"last":hist[-1][1][:10],
            "ai_trailers":ai_trailers(repo),"points":pts}

if __name__=="__main__":
    which=sys.argv[1] if len(sys.argv)>1 else None
    out={}
    for name,repo in REPOS.items():
        if which and name!=which: continue
        out[name]=run_repo(name,repo)
        r=out[name]
        print(f"\n### {name}  ({r['commits_total']} commits, {r['first']} → {r['last']})  AI-trailers={r['ai_trailers']}")
        print(f"{'date':12}{'n_funcs':>8}{'redund':>8}{'clusters':>9}{'dup_ratio':>10}")
        for p in r["points"]:
            if "error" in p: print(f"{p['date']:12}{'ERR:'+p['error']:>35}")
            else: print(f"{p['date']:12}{p['n']:>8}{p['redundant']:>8}{p['clusters']:>9}{p['dup_ratio']:>10}")
    json.dump(out, open("longitudinal_out.json","w"), indent=1)

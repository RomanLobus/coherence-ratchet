"""VOL1 — volatility-gated dependency-cycle ratchet.

Hypothesis (Khononov, *Balancing Coupling*, 2025): "coupling only matters where it meets
volatility"; "the goal is not to minimise coupling." A raw cycle-ratio ratchet flags every
interval in which `cycle_ratio` rises, including cycles that form among frozen/legacy modules
that no longer change — those are false-positive backsliding flags. Weighting (or gating) the
cycle signal by per-module **volatility** (normalised git commit-frequency) should suppress the
frozen-module false positives without missing live decay (cycles that recruit modules people
are still editing).

This is a standalone probe. It imports the shipped `coherence_ratchet` package (does not edit
it) and reuses:
  - archmetrics._collect_modules / _edges_for / _tarjan  (static module graph + SCCs)
  - probe_hyperliminal.cochange                          (per-module commit-frequency = volatility)
  - longitudinal_arch's history-sweep pattern            (16 first-parent samples over history)

Operationalisation (stated explicitly, see the write-up):
  * VOLATILITY(m) = commits touching module m over the repo's full history, normalised to [0,1]
    by dividing by the max per-module commit count in that repo (max-normalisation, per repo).
    Computed ONCE over full history (`git log --all`), then read at each sample — a module's
    lifetime churn, the Khononov "how often does this change" axis.
  * At each history sample we extract the SET OF CYCLIC MODULES (modules in an SCC of size > 1),
    not just the ratio, using archmetrics' own graph + Tarjan.
  * RAW FLAG on interval (t -> t+1): cycle_ratio(t+1) > cycle_ratio(t)   [the baseline ratchet]
  * GATED FLAG: flag the interval only if at least one module that NEWLY ENTERS a cycle at t+1
    (in a cycle at t+1, not at t) has VOLATILITY > FROZEN_THRESHOLD. If every newly-cyclic module
    is frozen (volatility <= threshold), the interval is SUPPRESSED.
  * A suppressed interval is a TRUE-POSITIVE SUPPRESSION iff all its newly-cyclic modules are
    genuinely frozen; the probe reports the volatility of the newly-cyclic modules so this is
    checkable rather than asserted.

Deterministic: fixed sample count, fixed threshold, `--all` history (survives detached HEAD).
"""
from __future__ import annotations

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coherence_ratchet import archmetrics as am  # noqa: E402
from probe_hyperliminal import cochange  # noqa: E402

GH = os.environ.get("CR_CORPUS", "/tmp/gh-test")
REPOS = {"flask": "src/flask", "requests": "src/requests", "httpie": "httpie"}
SRC = {  # candidate package dirs over history (first existing wins)
    "flask": ["src/flask", "flask"],
    "requests": ["src/requests", "requests"],
    "httpie": ["httpie"],
}
N_SAMPLES = 16
FROZEN_THRESHOLD = 0.05  # normalised volatility <= this => "frozen" (legacy) module


# --- git helpers (mirror longitudinal_arch) ---------------------------------

def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args],
                          capture_output=True, text=True).stdout.strip()


def history(repo):
    # HEAD is detached here with no branch reachable via --first-parent HEAD, so sweep --all
    # (the same choice the shipped probes make). --first-parent keeps the mainline spine and
    # avoids double-counting merged topic branches.
    out = git(repo, "log", "--all", "--first-parent", "--format=%H|%cI", "--reverse")
    return [tuple(l.split("|")) for l in out.splitlines() if "|" in l]


def sample(seq, n):
    if len(seq) <= n:
        return list(range(len(seq)))
    return [round(i * (len(seq) - 1) / (n - 1)) for i in range(n)]


# --- static graph -> cyclic module set at a tree ----------------------------

def cyclic_modules(root):
    """set of modules caught in some dependency cycle (SCC size > 1), + n_modules + cycle_ratio.

    Reuses archmetrics' collectors and Tarjan so it matches measure_arch exactly."""
    mods = am._collect_modules(root)
    internal = set(mods)
    pkg = os.path.basename(os.path.normpath(root))
    adj = {m: set() for m in internal}
    for m, path in mods.items():
        adj[m] |= am._edges_for(path, m, pkg, internal)
    sccs = am._tarjan(list(internal), adj)
    cyclic = set()
    for c in sccs:
        if len(c) > 1:
            cyclic |= set(c)
    n = len(internal)
    return cyclic, n, (len(cyclic) / n if n else 0.0)


def short(mod):
    return mod.split(".")[-1]


# --- volatility over full history -------------------------------------------

def volatility(repo, name):
    """normalised [0,1] per-module commit frequency over full history.

    Computed at the repo's *current* tree layout (abspath->module), then attributed over history
    via probe_hyperliminal.cochange's suffix matching (survives the src/ migration)."""
    srcdir = next((os.path.join(repo, c) for c in SRC[name]
                   if os.path.isdir(os.path.join(repo, c))), None)
    mods = am._collect_modules(srcdir)
    abs2mod = {os.path.abspath(p): m for m, p in mods.items()}
    changes, _pair, _blast, _n = cochange(repo, srcdir, abs2mod, max_commits=8000)
    if not changes:
        return {}, 0
    mx = max(changes.values())
    vol = {m: c / mx for m, c in changes.items()}
    return vol, mx


# --- the sweep --------------------------------------------------------------

def run_repo(name):
    repo = os.path.join(GH, name)
    hist = history(repo)
    cur = git(repo, "symbolic-ref", "--short", "-q", "HEAD") or git(repo, "rev-parse", "HEAD")
    vol, mx_commits = volatility(repo, name)  # full-history volatility, before checkouts

    idxs = sample(hist, N_SAMPLES)
    samples = []  # (date, sha, cyclic_set, n, ratio)
    for k in idxs:
        sha, date = hist[k]
        subprocess.run(["git", "-C", repo, "checkout", "-q", "-f", sha],
                       capture_output=True, text=True)
        srcdir = next((os.path.join(repo, c) for c in SRC[name]
                       if os.path.isdir(os.path.join(repo, c))), None)
        if not srcdir:
            samples.append((date[:10], sha[:8], set(), 0, 0.0))
            continue
        cyc, n, ratio = cyclic_modules(srcdir)
        samples.append((date[:10], sha[:8], cyc, n, ratio))
    subprocess.run(["git", "-C", repo, "checkout", "-q", "-f", cur],
                   capture_output=True, text=True)

    raw_flags = []
    gated_flags = []
    suppressed = []  # intervals raw-flagged but gated-suppressed, with evidence
    for i in range(len(samples) - 1):
        d0, s0, cyc0, n0, r0 = samples[i]
        d1, s1, cyc1, n1, r1 = samples[i + 1]
        if r1 > r0 + 1e-9:  # RAW backsliding flag
            raw_flags.append(i)
            newly = cyc1 - cyc0  # modules that newly entered a cycle
            newly_vol = sorted(((vol.get(m, 0.0), short(m)) for m in newly), reverse=True)
            live = [m for m in newly if vol.get(m, 0.0) > FROZEN_THRESHOLD]
            if live:  # at least one non-frozen module joined a cycle => keep the flag
                gated_flags.append(i)
                continue
            # no live module joined a cycle -> suppress. Two sub-cases, kept distinct:
            if len(newly) == 0:
                # cycle_ratio rose with NO new module entering a cycle: the ratio moved because
                # the denominator (n_modules) shrank or the graph was reshaped, not because a
                # module backslid. Not a frozen-module suppression and not a decay miss.
                kind = "denominator-shift"
                tp = None
            else:
                # every module that newly entered a cycle is frozen -> true-positive suppression
                kind = "all-frozen"
                tp = True
            suppressed.append({
                "interval": f"{d0}->{d1}",
                "cycle_ratio": f"{r0:.3f}->{r1:.3f}",
                "n_mods": f"{n0}->{n1}",
                "newly_cyclic": [(round(v, 3), nm) for v, nm in newly_vol],
                "n_newly": len(newly),
                "kind": kind,
                "true_positive_suppression": tp,
            })
    return {
        "name": name, "commits_total": len(hist),
        "first": hist[0][1][:10], "last": hist[-1][1][:10],
        "n_intervals": len(samples) - 1,
        "raw": len(raw_flags), "gated": len(gated_flags),
        "suppressed": suppressed,
        "max_commits_per_module": mx_commits,
        "n_modules_with_volatility": len(vol),
        "frozen_share": round(
            sum(1 for v in vol.values() if v <= FROZEN_THRESHOLD) / len(vol), 3) if vol else 0.0,
        "samples": samples,
    }


# --- STRETCH: per-edge balance/friction score ------------------------------

def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx == 0 or syy == 0:
        return None
    return sxy / (sxx * syy) ** 0.5


def balance_analysis(name):
    """STRETCH. Per-edge 'friction' ~ integration_strength x distance x volatility, at the
    CURRENT tree (Khononov: a coupling is costly when strong integration meets high distance and
    high volatility). Then correlate a per-module friction aggregate against (a) whether the
    module sits in a dependency cycle and (b) its connascence-of-meaning participation. Honest,
    exploratory, current-snapshot only.

    Operationalisation of the three axes, deterministically and cheaply:
      integration_strength(edge a->b): number of distinct import statements in a that reach b
                                       (approx of how much of a's contract leans on b) -> here 1
                                       per resolved edge, refined by counting import occurrences.
      distance(a, b): package-tree hops between a and b = depth(a) + depth(b) - 2*common_prefix
                      (closest-common-ancestor depth). Local (same package) = small; cross = large.
      volatility(a): max-normalised commit frequency of the *source* module (the one that would
                     have to change).
    """
    from coherence_ratchet import signals as sig

    repo = os.path.join(GH, name)
    srcdir = next((os.path.join(repo, c) for c in SRC[name]
                   if os.path.isdir(os.path.join(repo, c))), None)
    vol, _mx = volatility(repo, name)
    mods = am._collect_modules(srcdir)
    internal = set(mods)
    pkg = os.path.basename(os.path.normpath(srcdir))

    # integration strength: count import statements in `a` that resolve to internal target `b`
    import ast

    def edge_strengths(path, mod):
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError, OSError):
            return {}
        from collections import defaultdict
        strength = defaultdict(int)
        base = mod.rsplit(".", 1)[0] if "." in mod else mod
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    t = am._resolve(a.name, internal)
                    if t and t != mod:
                        strength[t] += 1
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    up = base.split(".")
                    up = up[: len(up) - (node.level - 1)] if node.level > 1 else up
                    target = ".".join(up + ([node.module] if node.module else []))
                else:
                    target = node.module or ""
                t = am._resolve(target, internal)
                if t and t != mod:
                    strength[t] += 1
                for a in node.names:
                    t2 = am._resolve((target + "." + a.name) if target else a.name, internal)
                    if t2 and t2 != mod:
                        strength[t2] += 1
        return strength

    def distance(a, b):
        pa, pb = a.split("."), b.split(".")
        common = 0
        for x, y in zip(pa, pb):
            if x == y:
                common += 1
            else:
                break
        return (len(pa) - 1) + (len(pb) - 1) - 2 * (common - 1)  # -1: drop shared pkg root

    # per-edge friction, aggregated to the source module
    from collections import defaultdict
    mod_friction = defaultdict(float)
    n_edges = 0
    for mod, path in mods.items():
        for tgt, strength in edge_strengths(path, mod).items():
            d = max(distance(mod, tgt), 1)
            f = strength * d * vol.get(mod, 0.0)
            mod_friction[mod] += f
            n_edges += 1

    # cycle membership at current tree
    cyc, _n, _r = cyclic_modules(srcdir)
    # connascence participation: how many shared literals each module partakes in.
    # connascence_of_meaning names modules relative to root (e.g. "sansio.app"); archmetrics
    # names them package-prefixed (e.g. "flask.sansio.app"). Join by stripping the "<pkg>." prefix.
    _cnt, conn_rows = sig.connascence_of_meaning(srcdir)
    conn_part = defaultdict(int)
    for row in conn_rows:
        for m in row["modules"]:
            conn_part[m] += 1

    def rel(m):  # "flask.sansio.app" -> "sansio.app"; "flask" -> ""
        return m[len(pkg) + 1:] if m.startswith(pkg + ".") else ("" if m == pkg else m)

    common_mods = [m for m in internal if m in vol]
    fr = [mod_friction.get(m, 0.0) for m in common_mods]
    incyc = [1.0 if m in cyc else 0.0 for m in common_mods]
    conn = [float(conn_part.get(rel(m), 0)) for m in common_mods]
    return {
        "name": name, "n_modules": len(common_mods), "n_edges": n_edges,
        "corr_friction_vs_incycle": _pearson(fr, incyc),
        "corr_friction_vs_connascence": _pearson(fr, conn),
        "mean_friction_cyclic": (sum(f for f, c in zip(fr, incyc) if c) /
                                 max(sum(incyc), 1)),
        "mean_friction_acyclic": (sum(f for f, c in zip(fr, incyc) if not c) /
                                  max(len(fr) - sum(incyc), 1)),
    }


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else None
    stretch = "--stretch" in sys.argv
    for name in REPOS:
        if which and name != which and not which.startswith("--"):
            continue
        repo = os.path.join(GH, name)
        if not os.path.isdir(repo):
            print(f"### {name}: repo missing at {repo}")
            continue
        r = run_repo(name)
        print(f"\n### {name}  ({r['commits_total']} commits, {r['first']} -> {r['last']})")
        print(f"  modules with volatility: {r['n_modules_with_volatility']}  "
              f"max commits/module: {r['max_commits_per_module']}  "
              f"frozen share (<= {FROZEN_THRESHOLD}): {r['frozen_share']}")
        print(f"  RAW backsliding flags:   {r['raw']} / {r['n_intervals']} intervals")
        print(f"  GATED (volatility) flags: {r['gated']} / {r['n_intervals']} intervals")
        print(f"  suppressed: {r['raw'] - r['gated']}")
        for s in r["suppressed"]:
            label = {"all-frozen": "TRUE-POS (all newly-cyclic frozen)",
                     "denominator-shift": "NEUTRAL (no module entered a cycle; n_mods "
                                          f"{s['n_mods']})"}[s["kind"]]
            print(f"    - {s['interval']}  cycle_ratio {s['cycle_ratio']}  "
                  f"newly-cyclic={s['newly_cyclic'][:6]}  [{label}]")

    if stretch:
        print("\n\n## STRETCH — per-edge balance/friction score (current tree)")
        print("  friction(edge) = integration_strength x distance x volatility(source)")
        for name in REPOS:
            if which and name != which and not which.startswith("--"):
                continue
            if not os.path.isdir(os.path.join(GH, name)):
                continue
            b = balance_analysis(name)
            def fmt(x):
                return "n/a" if x is None else f"{x:+.3f}"
            print(f"\n  ### {name}  ({b['n_modules']} modules, {b['n_edges']} edges)")
            print(f"    corr(friction, in-cycle)      = {fmt(b['corr_friction_vs_incycle'])}")
            print(f"    corr(friction, connascence)   = {fmt(b['corr_friction_vs_connascence'])}")
            print(f"    mean friction  cyclic={b['mean_friction_cyclic']:.2f}  "
                  f"acyclic={b['mean_friction_acyclic']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

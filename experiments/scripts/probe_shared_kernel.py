"""EXP2 — shared-kernel seam detector (context-map classification; Khononov,
*Learning Domain-Driven Design*, 2021).

DDD context maps classify the seams between bounded contexts. Two are load-bearing for
risk:
  - SHARED KERNEL: a model/type defined in one module and imported/used by >= 2 other
    modules. A change to it cascades to every consumer — the highest-risk seam, because
    the shared type is a coupling point nobody owns cleanly.
  - ANTICORRUPTION LAYER (ACL): a module that translates/wraps another's model rather
    than importing its types raw — it absorbs change instead of propagating it.

Operationalisation (deterministic, stdlib-only, reuses the shipped package):
  - Import graph from `archmetrics._collect_modules` + `_edges_for`.
  - A "type" = a top-level class defined in exactly one internal module (its home).
    (Entity/dataclass/TypedDict/NamedTuple shapes from `selfmodel._explicit_entities`
    are a subset; we widen to all top-level classes because a shared kernel is any
    shared *model*, not only a dataclass.)
  - CONSUMERS of a type = internal modules that import os
import that exact name from its home
    module (`from <home> import <Type>`, or `import <home>` then reference `home.Type`).
  - SHARED-KERNEL SEAM: a type with >= 2 distinct consumer modules. Each such type
    induces consumer-pairs (both joined through the shared type) — the seams.
  - ACL heuristic: a consumer module is ACL-ish for a home if it imports the home's
    type AND defines its own wrapper/adapter class or *-Adapter/*-Wrapper naming and
    re-exposes a translated shape. This is approximate; reported as a count, flagged.

Risk test: are consumer-pairs joined by a shared-kernel type more CO-CHANGING than
baseline module pairs? Reuses `probe_hyperliminal.cochange` for per-pair co-change
(Jaccard). Reports mean/median Jaccard for shared-kernel pairs vs all other co-changing
pairs, plus a rank-sum style comparison. Honest about small-n.
"""
import ast, os, sys
from collections import defaultdict
from statistics import mean, median
sys.path.insert(0, os.path.dirname(__file__))
from coherence_ratchet import archmetrics as am
from probe_hyperliminal import static_graph, cochange


def _top_level_classes(mods):
    """home module -> set of class names defined at top level there.
    Also returns name -> set(home modules) to spot names defined in >1 place."""
    home = defaultdict(set)          # module -> {ClassName}
    defined_in = defaultdict(set)    # ClassName -> {module}
    for m, p in mods.items():
        try:
            tree = ast.parse(open(p, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        for n in tree.body:
            if isinstance(n, ast.ClassDef):
                home[m].add(n.name)
                defined_in[n.name].add(m)
    return home, defined_in


def _imported_names(path, mod, pkg, internal):
    """Which (internal_home_module, imported_symbol) pairs this module pulls in.

    Captures `from <home> import Sym` (Sym may be a class) and `import <home>`
    (then any attribute use of home.Sym is a use, approximated by recording home)."""
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except (SyntaxError, UnicodeDecodeError, OSError):
        return []
    base = mod.rsplit(".", 1)[0] if "." in mod else mod
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                up = base.split(".")
                up = up[: len(up) - (node.level - 1)] if node.level > 1 else up
                target = ".".join(up + ([node.module] if node.module else []))
            else:
                target = node.module or ""
            home = am._resolve(target, internal)
            if home and home != mod:
                for a in node.names:
                    out.append((home, a.name))
            # `from pkg import submod` where submod is itself a module: symbol may be a type living there
            for a in node.names:
                h2 = am._resolve((target + "." + a.name) if target else a.name, internal)
                if h2 and h2 != mod:
                    out.append((h2, None))   # module import; specific symbol unknown
        elif isinstance(node, ast.Import):
            for a in node.names:
                h = am._resolve(a.name, internal)
                if h and h != mod:
                    out.append((h, None))
    return out


def _acl_ish(path):
    """Heuristic: module defines a class whose name ends in Adapter/Wrapper/Codec/
    Translator/Mapper, or has 'to_'/'from_'/'adapt'/'convert' functions — a translation
    seam. Approximate; used only for a flagged count."""
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except (SyntaxError, UnicodeDecodeError, OSError):
        return False
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and n.name.lower().rstrip("s").endswith(
                ("adapter", "wrapper", "codec", "translator", "mapper")):
            return True
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nm = n.name.lower()
            if nm.startswith(("to_", "from_", "adapt", "convert")):
                return True
    return False


def analyse(name, repo, srcsub, min_consumers=2):
    root = os.path.join(repo, srcsub)
    mods = am._collect_modules(root)
    internal = set(mods)
    pkg = os.path.basename(os.path.normpath(root))
    home, defined_in = _top_level_classes(mods)

    # type name -> home module (only names defined in exactly one internal module)
    single_home = {nm: next(iter(hs)) for nm, hs in defined_in.items() if len(hs) == 1}

    # consumers[(home, Type)] = set(consumer modules) that import Type from home
    consumers = defaultdict(set)
    module_imports_home = defaultdict(set)   # home -> {consumer modules importing it at all}
    for m, p in mods.items():
        for h, sym in _imported_names(p, m, pkg, internal):
            module_imports_home[h].add(m)
            if sym and sym in home.get(h, ()):        # imported an actual class defined there
                consumers[(h, sym)].add(m)

    # shared-kernel types: a defined type with >= min_consumers consumer modules
    kernels = []
    for (h, sym), cons in consumers.items():
        cons = {c for c in cons if c != h}
        if len(cons) >= min_consumers:
            kernels.append((sym, h, sorted(cons)))
    kernels.sort(key=lambda k: -len(k[2]))

    # ACL count: how many modules look like translation seams
    acl = [m for m, p in mods.items() if _acl_ish(p)]

    # --- risk test: co-change of shared-kernel consumer-pairs vs baseline ------
    _, static_edges, abs2mod = static_graph(root)
    changes, pair, blast, n_commits = cochange(repo, root, abs2mod)

    # build the set of module pairs joined by a shared kernel (consumer x consumer, and consumer x home)
    kernel_pairs = set()
    for sym, h, cons in kernels:
        members = sorted(set(cons) | {h})
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                kernel_pairs.add(frozenset((members[i], members[j])))

    def jac(fs):
        a, b = tuple(fs)
        u = changes[a] + changes[b] - pair.get(fs, 0)
        return pair.get(fs, 0) / u if u else 0.0

    # only compare pairs that co-changed at least once (both modules have history)
    cochanged = {fs for fs, c in pair.items() if c > 0}
    k_pairs = [fs for fs in kernel_pairs if fs in cochanged]
    base_pairs = [fs for fs in cochanged if fs not in kernel_pairs]
    kj = [jac(fs) for fs in k_pairs]
    bj = [jac(fs) for fs in base_pairs]

    print(f"\n### {name} — {len(internal)} modules, {len(single_home)} single-home types, "
          f"{n_commits} source commits")
    print(f"  SHARED-KERNEL seams (type used by >= {min_consumers} consumer modules): {len(kernels)}")
    for sym, h, cons in kernels[:8]:
        print(f"    {sym:<22} home={h.split('.')[-1]:<16} consumers={len(cons)}  "
              f"[{', '.join(c.split('.')[-1] for c in cons[:4])}{'...' if len(cons) > 4 else ''}]")
    print(f"  ACL-ish (translation-seam) modules: {len(acl)}  "
          f"[{', '.join(m.split('.')[-1] for m in acl[:6])}{'...' if len(acl) > 6 else ''}]")
    print(f"  co-change risk test:")
    print(f"    shared-kernel consumer-pairs that co-changed: {len(k_pairs)} of {len(kernel_pairs)}")
    print(f"    baseline co-changing pairs: {len(base_pairs)}")
    if kj and bj:
        # fraction of baseline pairs with Jaccard below the kernel-pair median (a crude effect read)
        km, bm = median(kj), median(bj)
        print(f"    mean Jaccard  kernel={mean(kj):.3f}  baseline={mean(bj):.3f}")
        print(f"    median Jaccard kernel={km:.3f}  baseline={bm:.3f}")
        # rank-sum: probability a random kernel pair out-co-changes a random baseline pair
        wins = sum(1 for x in kj for y in bj if x > y) + 0.5 * sum(1 for x in kj for y in bj if x == y)
        auc = wins / (len(kj) * len(bj))
        print(f"    P(kernel pair co-changes more than baseline pair) = {auc:.2f}  (0.5 = no effect)")
    else:
        print(f"    insufficient co-changing pairs to test (kernel={len(kj)}, baseline={len(bj)})")
    return {"kernels": len(kernels), "acl": len(acl), "n": len(internal)}


if __name__ == "__main__":
    GH = os.environ.get("CR_CORPUS", "/tmp/gh-test")
    targets = {"requests": "src/requests", "flask": "src/flask", "httpie": "httpie"}
    which = sys.argv[1] if len(sys.argv) > 1 else None
    for nm, sub in targets.items():
        if which and nm != which:
            continue
        repo = os.path.join(GH, nm)
        if os.path.isdir(os.path.join(repo, sub)):
            analyse(nm, repo, sub)
        else:
            print(f"{nm}: {sub} missing")

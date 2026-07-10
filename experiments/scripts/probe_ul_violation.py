"""EXP3 — ubiquitous-language / bounded-context violation detector.

Khononov (*Learning Domain-Driven Design*, 2021): within a bounded context each term
should have "one and only one meaning." A **ubiquitous-language violation** is the same
domain term (an entity/class/type name, or a dict-shape "kind") resolving to
*structurally divergent shapes* across different modules/sub-packages **without an
intervening translation** — the KeyError-class interoperability break: module A builds a
`Foo` with one field set, module B reads a `Foo` with an incompatible field set, and no
adapter reconciles them.

This extends the existing entity-coherence signal (see experiments/entity-coherence.md),
which flags one entity fragmented across an *independent-agent* codebase. Here the unit is
the *established* codebase: group every entity/dict shape by normalised name across all
modules, flag names whose field/key sets are incompatible in different modules, and check
whether a translation/adapter module sits on the path between them.

Operationalisation (deterministic, stdlib-only, reuses the shipped package):
  - Shapes come from `selfmodel._explicit_entities` (dataclass/TypedDict/NamedTuple:
    name + fields + module) and `selfmodel._dict_shapes` (implicit dict shapes:
    base name + per-site key sets).
  - Group by NORMALISED name (lowercased, plural-stripped). A term is a candidate only if
    it looks like a *domain term*, not a generic container — generic accumulator names
    (kwargs/options/self/data/params/headers/result/...) are excluded, because a dict
    called `kwargs` holding different keys in two modules is not a shared term, it is two
    unrelated local option bags.
  - A term is a VIOLATION if it appears in >= 2 different modules with >= 2 structurally
    incompatible field/key sets (neither a subset of the other).
  - TRANSLATION check: is either module (or a module on the import os
import path between them)
    ACL-ish — defines an *Adapter/*Wrapper/*Codec/*Translator/*Mapper class or
    to_/from_/adapt/convert functions? If so the divergence is *mediated*, not a raw break.
"""
import ast, os, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from coherence_ratchet import archmetrics as am
from coherence_ratchet import selfmodel as sm

# names that are containers/plumbing, not domain terms — a shape mismatch here is not a UL violation
GENERIC = {
    "kwargs", "args", "options", "opts", "self", "data", "params", "config",
    "result", "results", "response", "request", "headers", "extra", "extras",
    "context", "ctx", "env", "environ", "meta", "info", "state", "payload",
    "obj", "item", "items", "value", "values", "kw", "d", "cls", "session",
    "cookie", "morsel", "record", "row", "entry", "attrs", "props", "settings",
}


def _normalise(name):
    n = name.strip().lower()
    if n.endswith("ies") and len(n) > 4:
        n = n[:-3] + "y"
    elif n.endswith("es") and len(n) > 4:
        n = n[:-2]
    elif n.endswith("s") and len(n) > 3:
        n = n[:-1]
    return n


def _acl_ish(path):
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except (SyntaxError, UnicodeDecodeError, OSError):
        return False
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and n.name.lower().rstrip("s").endswith(
                ("adapter", "wrapper", "codec", "translator", "mapper")):
            return True
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if n.name.lower().startswith(("to_", "from_", "adapt", "convert")):
                return True
    return False


def _incompatible(sets):
    """True if any two field/key sets are structurally incompatible (neither subset)."""
    sets = [s for s in sets if s]
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            a, b = sets[i], sets[j]
            if not (a <= b or b <= a):
                return True
    return False


def analyse(name, repo, srcsub):
    root = os.path.join(repo, srcsub)
    mods = am._collect_modules(root)
    modpaths = {m.split(".", 1)[1] if "." in m else m: p for m, p in mods.items()}  # bare -> path

    # normalised term -> list of (module, kind, frozenset(fields/keys))
    term = defaultdict(list)
    for e in sm._explicit_entities(root):
        if e["name"].lower() in GENERIC:
            continue
        term[_normalise(e["name"])].append((e["module"], e["kind"], frozenset(e["fields"])))
    for d in sm._dict_shapes(root):
        if d["name"].lower() in GENERIC:
            continue
        for mod, keys in d["per_site_keys"].items():
            term[_normalise(d["name"])].append((mod, "dict-shape", frozenset(keys)))

    violations = []
    for t, occ in term.items():
        modules = {m for m, _, _ in occ}
        if len(modules) < 2:
            continue
        # merge shapes per module (a module may have >1 occurrence)
        per_mod = defaultdict(set)
        for m, k, fs in occ:
            per_mod[m] |= set(fs)
        shapes = [frozenset(v) for v in per_mod.values()]
        if not _incompatible(shapes):
            continue
        # translation present between any of the involved modules?
        translated = any(_acl_ish(modpaths.get(m, "")) for m in per_mod if m in modpaths)
        violations.append((t, sorted(per_mod), translated,
                           {m: sorted(s)[:6] for m, s in per_mod.items()}))

    print(f"\n### {name} — {len(term)} candidate domain terms (generic names excluded), "
          f"{len(violations)} UL violations")
    for t, mods_, translated, shapes in violations:
        tag = "  [translation present]" if translated else "  [NO translation — raw break]"
        print(f"    '{t}' in {mods_}{tag}")
        for m, ks in shapes.items():
            print(f"        {m}: {ks}")
    return {"terms": len(term), "violations": len(violations)}


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

"""The derived, queryable self-model — the keystone artefact of the method.

The book's argument: an agent should move a change *toward* a known shape, not add to a pile. That
shape must not be hand-curated (hand-maintained maps rot — RES6), so it is **derived from the code**
and regenerated on demand. `derive(root)` reads a source tree and produces a structured model:

  - modules + dependency structure (who imports whom, fan-in/out, a role heuristic)
  - functions (name, args, calls, docstring) — the index the concept queries run over
  - entities / canonical shapes — dataclasses/TypedDict/NamedTuple, and implicit dict shapes,
    with the modal shape and the sites that diverge from it
  - conventions / values — significant literals shared across modules (connascence of meaning)
  - helpers — clusters of near-duplicate functions, i.e. "this already exists, reuse it"

Everything here is deterministic and stdlib-only. The optional LLM matcher lives in query.py and is
never required. The steward *ratifies and judges* this model; the tool never asks a human to refresh it.
"""
from __future__ import annotations

import ast
import json
import os
import re
from collections import Counter, defaultdict

from . import archmetrics as am
from . import metrics as fm
from .signals import connascence_of_meaning

SELFMODEL_VERSION = 1


def _name_tokens(name: str) -> list[str]:
    """Split an identifier into lowercase concept tokens (snake_case and camelCase)."""
    parts = re.split(r"[_\W]+", name)
    out = []
    for p in parts:
        out.extend(re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", p) or [p])
    return [t.lower() for t in out if t]


def _docline(node: ast.AST) -> str:
    doc = ast.get_docstring(node)
    return doc.strip().splitlines()[0] if doc else ""


def _call_names(node: ast.AST) -> list[str]:
    calls = []
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                calls.append(f.id)
            elif isinstance(f, ast.Attribute):
                calls.append(f.attr)
    return calls


# --- modules ----------------------------------------------------------------

def _module_structure(root: str) -> list[dict]:
    mods = am._collect_modules(root)
    internal = set(mods)
    pkg = os.path.basename(os.path.normpath(root))
    depends = {m: sorted(am._edges_for(p, m, pkg, internal) - {m}) for m, p in mods.items()}
    fan_in = {m: 0 for m in mods}
    for m, deps in depends.items():
        for t in deps:
            fan_in[t] = fan_in.get(t, 0) + 1

    # am names modules with the package prefix (billing.money) for import resolution; the function
    # and entity indexes use bare names relative to root (money). Strip the prefix so cross-references
    # between the module graph and the function/helper indexes line up.
    def bare(name: str) -> str:
        return name[len(pkg) + 1:] if name.startswith(pkg + ".") else name

    out = []
    for m in sorted(mods):
        fo, fi = len(depends[m]), fan_in.get(m, 0)
        if fo == 0 and fi > 0:
            role = "foundation"       # depended upon, depends on nothing internal
        elif fi == 0 and fo > 0:
            role = "entry"            # depends on others, nobody depends on it
        elif fi == 0 and fo == 0:
            role = "isolated"
        else:
            role = "intermediate"
        out.append({"module": bare(m), "depends_on": [bare(d) for d in depends[m]],
                    "fan_in": fi, "fan_out": fo, "role": role})
    return out


# --- functions --------------------------------------------------------------

def _functions(root: str) -> list[dict]:
    out = []
    for path in fm._iter_py_files(root):
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        mod = fm._module_name(root, path)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue
                out.append({
                    "qualname": f"{mod}.{node.name}",
                    "module": mod,
                    "name": node.name,
                    "args": [a.arg for a in node.args.args if a.arg not in ("self", "cls")],
                    "calls": sorted(set(_call_names(node))),
                    "doc": _docline(node),
                    "tokens": sorted(set(_name_tokens(node.name))),
                })
    out.sort(key=lambda f: f["qualname"])
    return out


# --- entities / canonical shapes --------------------------------------------

_STRUCTURAL_BASES = {"TypedDict", "NamedTuple"}


def _explicit_entities(root: str) -> list[dict]:
    out = []
    for path in fm._iter_py_files(root):
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        mod = fm._module_name(root, path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            is_dc = any(am._attr_name(d).split(".")[-1] == "dataclass" for d in node.decorator_list)
            base_names = {am._attr_name(b).split(".")[-1] for b in node.bases}
            kind = None
            if is_dc:
                kind = "dataclass"
            elif base_names & _STRUCTURAL_BASES:
                kind = (base_names & _STRUCTURAL_BASES).pop()
            if not kind:
                continue
            fields = []
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    fields.append(item.target.id)
                elif isinstance(item, ast.Assign):
                    for t in item.targets:
                        if isinstance(t, ast.Name):
                            fields.append(t.id)
            out.append({"name": node.name, "kind": kind, "module": mod, "fields": sorted(set(fields))})
    return out


def _dict_shapes(root: str) -> list[dict]:
    """Implicit entity shapes: base names subscripted with string-literal keys, aggregated across
    modules. Records the key frequency so a query can report the canonical shape and its divergences."""
    per_name_keys: dict = defaultdict(lambda: defaultdict(Counter))  # base -> module -> Counter(keys)
    for path in fm._iter_py_files(root):
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        mod = fm._module_name(root, path)
        for n in ast.walk(tree):
            if (isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
                    and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str)):
                per_name_keys[n.value.id][mod][n.slice.value] += 1
    out = []
    for base, by_mod in per_name_keys.items():
        keyfreq: Counter = Counter()
        sites = sorted(by_mod)
        for mod, keys in by_mod.items():
            for k in keys:
                keyfreq[k] += 1
        # Only interesting when the same shape appears in >=2 sites or has >=2 keys.
        if len(sites) < 2 and sum(keyfreq.values()) < 2:
            continue
        out.append({
            "name": base,
            "kind": "dict-shape",
            "sites": sites,
            "key_frequency": dict(keyfreq),
            "per_site_keys": {m: sorted(k) for m, k in by_mod.items()},
        })
    out.sort(key=lambda e: (-len(e["sites"]), e["name"]))
    return out


# --- helpers (reuse candidates) ---------------------------------------------

def _helpers(root: str) -> list[dict]:
    snap = fm.measure(root)
    out = []
    for cluster in snap.clusters:
        # concept = the name token shared by the most members
        tokens = Counter()
        for q in cluster:
            for t in _name_tokens(q.rsplit(".", 1)[-1]):
                tokens[t] += 1
        concept = tokens.most_common(1)[0][0] if tokens else ""

        # The canonical site to reuse is the one that IS the concept, not an arbitrary alphabetical
        # first: prefer a member whose function name or module equals the concept, then the one with
        # the most generic (fewest-token) name, tie-broken alphabetically.
        def rank(q):
            mod, _, fn = q.rpartition(".")
            fn_tokens = _name_tokens(fn)
            score = 0
            if fn == concept:
                score += 4
            if mod.split(".")[-1] == concept:
                score += 3
            if fn_tokens == [concept]:
                score += 2
            return (-score, len(fn_tokens), q)

        ordered = sorted(cluster, key=rank)
        canonical = ordered[0]
        out.append({
            "concept": concept,
            "canonical": canonical,           # the site to reuse
            "duplicates": [q for q in cluster if q != canonical],
        })
    return out


# --- top level --------------------------------------------------------------

def derive(root: str) -> dict:
    conc_count, conc_rows = connascence_of_meaning(root)
    entities = _explicit_entities(root) + _dict_shapes(root)
    return {
        "selfmodel_version": SELFMODEL_VERSION,
        "root": os.path.normpath(root),
        "modules": _module_structure(root),
        "functions": _functions(root),
        "entities": entities,
        "conventions": [{"value": r["value"], "modules": r["modules"]} for r in conc_rows],
        "helpers": _helpers(root),
    }


def context_pack(model: dict) -> str:
    """Render the self-model as a compact grounding pack to feed an agent BEFORE it writes a change.

    This operationalises prevention-by-visibility: the full-context experiment showed surfacing the
    canonical shape drove reuse from 0/3 to 3/3, so handing an agent this pack is what turns
    "reuses if it happens to see it" into "reliably sees it" — the enabler of higher autonomy."""
    lines = ["# Coherence self-model — grounding for this subsystem",
             "# Read before writing a change. Reuse what is named here; do not reinvent it.", ""]

    helpers = model.get("helpers", [])
    if helpers:
        lines.append("## Reuse these canonical helpers (do not reimplement)")
        for h in helpers:
            dup = f"  — already duplicated in {', '.join(h['duplicates'])}" if h.get("duplicates") else ""
            lines.append(f"- `{h['concept']}` → reuse `{h['canonical']}`{dup}")
        lines.append("")

    entities = model.get("entities", [])
    if entities:
        lines.append("## Canonical entity shapes (match these; do not invent new key sets)")
        for e in entities:
            if e.get("kind") == "dict-shape":
                n = len(e["sites"])
                shared = sorted(k for k, c in e.get("key_frequency", {}).items() if c == n)
                lines.append(f"- `{e['name']}` (dict): shared keys {', '.join(shared) or '(none agreed)'}"
                             f"; seen in {', '.join(e['sites'])}")
            else:
                lines.append(f"- `{e['name']}` ({e.get('kind')}) in {e.get('module')}: "
                             f"{', '.join(e.get('fields', []))}")
        lines.append("")

    conventions = model.get("conventions", [])
    if conventions:
        lines.append("## Conventions / shared values (reuse the existing value; don't hardcode a new one)")
        for c in conventions[:20]:
            lines.append(f"- {c['value']}  (shared across {', '.join(c['modules'])})")
        lines.append("")

    modules = model.get("modules", [])
    if modules:
        lines.append("## Module layers (respect these dependency directions)")
        for m in modules:
            deps = f" → {', '.join(m['depends_on'])}" if m.get("depends_on") else ""
            lines.append(f"- {m['module']} [{m['role']}]{deps}")
    return "\n".join(lines) + "\n"


def write(root: str, out_path: str) -> dict:
    model = derive(root)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(model, f, indent=2, sort_keys=True)
        f.write("\n")
    return model


# --- CLI wiring (called from cli.py) ----------------------------------------

DEFAULT_MODEL = "coherence/selfmodel.json"


def register_cli(sub) -> None:
    p = sub.add_parser("selfmodel", help="derive or query the derived self-model")
    p.add_argument("action", choices=["derive", "query", "context"])
    p.add_argument("target", help="source path (derive/context) or a question (query)")
    p.add_argument("--model", default=DEFAULT_MODEL, help="path to selfmodel.json")
    p.add_argument("--llm", action="store_true", help="use the optional LLM matcher (needs an API key)")
    p.add_argument("--out", help="write output to this path (context)")
    p.add_argument("--json", action="store_true")


def run_cli(args) -> int:
    from . import query as q

    if args.action == "derive":
        model = write(args.target, args.model)
        print(f"self-model derived from {args.target} -> {args.model}")
        print(f"  modules: {len(model['modules'])}  functions: {len(model['functions'])}  "
              f"entities: {len(model['entities'])}  conventions: {len(model['conventions'])}  "
              f"helpers: {len(model['helpers'])}")
        return 0
    if args.action == "query":
        with open(args.model, encoding="utf-8") as f:
            model = json.load(f)
        result = q.answer(model, args.target, use_llm=args.llm)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            q.render(result)
        return 0
    if args.action == "context":
        # derive from the given source path (or load a saved model if the target is one)
        if args.target.endswith(".json") and os.path.exists(args.target):
            with open(args.target, encoding="utf-8") as f:
                model = json.load(f)
        else:
            model = derive(args.target)
        pack = context_pack(model)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(pack)
            print(f"grounding pack written to {args.out}")
        else:
            print(pack, end="")
        return 0
    return 2


if __name__ == "__main__":
    import sys

    print(json.dumps(derive(sys.argv[1]), indent=2, sort_keys=True))

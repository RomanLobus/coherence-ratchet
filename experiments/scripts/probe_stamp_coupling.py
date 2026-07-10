"""Probe: a deterministic detector for the Stamp Coupling antipattern.

Stamp coupling (Myers; catalogued as an architecture antipattern) is passing a whole data structure to
a consumer that needs only part of it. The consumer is then coupled to the entire shape — a change to
any field it does not use can still break it, and the contract hides what is really depended on.

The insight this probe tests: the derived self-model already records which keys of an entity each site
actually touches (`per_site_keys`). That data is a latent stamp-coupling detector. For each function
parameter that is an entity (a name the codebase treats as a structure with several keys), compare the
keys the function actually uses against the entity's full observed shape. A function that receives the
whole entity and uses a small fraction of it — especially if it also forwards the whole thing onward —
is a stamp-coupling candidate.

Deterministic, stdlib-only. This is a PROBE: run it on a fixture and on real repos, report the hits and
the false positives honestly, then decide whether it is worth promoting to a packaged signal.

    python3 probe_stamp_coupling.py <path>            # one tree
    python3 probe_stamp_coupling.py                   # fixture + requests/flask if present
"""
from __future__ import annotations

import ast
import math
import os
import sys
from collections import defaultdict

# An entity is a parameter name the codebase treats as a structure with at least this many distinct
# keys. Below it, a "dict" is more likely a small options bag than a domain entity.
MIN_ENTITY_KEYS = 3
# A site is a candidate when it uses at most this fraction of the entity's observed keys.
UNDERUSE_FRACTION = 0.34


def _iter_py(root):
    for dp, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {"__pycache__", ".git", "tests", "test"}]
        for fn in sorted(files):
            if fn.endswith(".py"):
                yield os.path.join(dp, fn)


def _keys_used_on(func: ast.AST, param: str):
    """Keys read from `param` inside `func`, split by access style, plus wholesale-forward.

    Returns (subscript_keys, attribute_keys, passed_whole). Subscript keys (order["id"]) are the
    data-contract reading of stamp coupling — passing a data structure and using little of it.
    Attribute keys (order.id) also cover service OBJECTS (request, app, ctx), which are passed around
    by design; treating those as stamp coupling is the main false-positive source, so the two are
    kept apart."""
    sub_keys = set()
    attr_keys = set()
    method_attrs = set()
    passed_whole = False
    for n in ast.walk(func):
        if (isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
                and n.value.id == param and isinstance(n.slice, ast.Constant)
                and isinstance(n.slice.value, str)):
            sub_keys.add(n.slice.value)
        elif isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == param:
            attr_keys.add(n.attr)
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and isinstance(n.func.value, ast.Name) and n.func.value.id == param):
            method_attrs.add(n.func.attr)
        if isinstance(n, ast.Call):
            args = list(n.args) + [k.value for k in n.keywords]
            if any(isinstance(a, ast.Name) and a.id == param for a in args):
                passed_whole = True
    return sub_keys, attr_keys - method_attrs, passed_whole


def detect(root: str, data_only: bool = True):
    """Detect stamp-coupling candidates. data_only=True restricts to string-subscript (data-contract)
    access — the reading with far fewer false positives on object-oriented code."""
    funcs = []  # (module, funcname, param, used_keys, passed_whole)
    shape = defaultdict(set)  # param base name -> union of all keys seen on it, anywhere
    for path in _iter_py(root):
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        mod = os.path.splitext(os.path.relpath(path, root))[0].replace(os.sep, ".")
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            params = [a.arg for a in node.args.args if a.arg not in ("self", "cls")]
            for p in params:
                sub, attr, whole = _keys_used_on(node, p)
                used = sub if data_only else (sub | attr)
                shape[p] |= used
                funcs.append((mod, node.name, p, used, whole))

    candidates = []
    for mod, fn, p, used, whole in funcs:
        full = shape[p]
        if len(full) < MIN_ENTITY_KEYS:
            continue                                    # not an entity
        if not used and not whole:
            continue                                    # doesn't touch it at all (e.g. unused arg)
        frac = len(used) / len(full)
        if frac <= UNDERUSE_FRACTION or (whole and len(used) <= 1):
            candidates.append({
                "site": f"{mod}.{fn}({p})",
                "uses": sorted(used),
                "of_full": sorted(full),
                "fraction": round(frac, 2),
                "passes_whole": whole,
            })
    candidates.sort(key=lambda c: (c["fraction"], -len(c["of_full"])))
    return candidates, {p: sorted(k) for p, k in shape.items() if len(k) >= MIN_ENTITY_KEYS}


def _report(name, root):
    print(f"\n### {name}  ({root})")
    if not os.path.isdir(root):
        print("  (not present)")
        return
    data_cands, data_ents = detect(root, data_only=True)
    all_cands, all_ents = detect(root, data_only=False)
    print(f"  data-contract mode:  entities {len(data_ents):>3}  candidates {len(data_cands):>3}")
    print(f"  incl. attributes:    entities {len(all_ents):>3}  candidates {len(all_cands):>3}  "
          f"(the noisier object reading)")
    for c in data_cands[:12]:
        forward = "  [forwards whole]" if c["passes_whole"] else ""
        print(f"  - {c['site']}: uses {c['uses'] or '(none)'} of {c['of_full']} "
              f"= {c['fraction']}{forward}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        _report(os.path.basename(sys.argv[1]), sys.argv[1])
    else:
        GH = os.environ.get("CR_CORPUS", "/tmp/gh-test")
        _report("fixture", os.path.join(os.path.dirname(__file__), "_fixtures", "stampy"))
        _report("requests", os.path.join(GH, "requests", "src", "requests"))
        _report("flask", os.path.join(GH, "flask", "src", "flask"))

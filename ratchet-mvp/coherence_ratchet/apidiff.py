"""Public-API signature diff — one distinct part of a decision packet.

Consolidation is exactly the class of change where agents break public contracts most:
Ferdous et al. (MSR 2026) measured 2-3x more contract breakage on refactor/chore work
(6.72%/9.35%) than on feat/fix. `compare` searches for behavioural divergence; this module
checks the cheaper, wider thing — whether the tree's public
*surface* (module-level functions and classes, their names and signatures) survived the
change. Optional consolidation-time check; deterministic, stdlib-only.

Scope, honestly: Python only; syntactic compatibility only (a signature can survive while
the semantics change — that requires separate evidence); one tree against one tree (no cross-repo
caller analysis). Public = not underscore-prefixed, honouring `__all__` when a module
declares one; modules under an underscore-prefixed path segment are private.

Verdict rules: a REMOVED public symbol is BREAKING; a CHANGED signature is BREAKING when
it removes/renames a parameter callers could pass, adds a new required parameter, drops a
default, or restricts how a parameter may be passed (positional-or-keyword -> keyword-only
or positional-only); appended optional parameters, added */** catch-alls and changed
default *values* are compatible (reported, not failed). ADDED symbols are compatible.
"""
from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field

# parameter kinds
POS = "pos"        # positional-only
PK = "pk"          # positional-or-keyword
VAR = "vararg"     # *args
KW = "kw"          # keyword-only
KWARG = "kwarg"    # **kwargs


@dataclass
class Param:
    kind: str
    name: str
    has_default: bool = False
    default: str = ""

    def render(self) -> str:
        d = f"={self.default}" if self.has_default else ""
        if self.kind == VAR:
            return f"*{self.name}"
        if self.kind == KWARG:
            return f"**{self.name}"
        return f"{self.name}{d}"


@dataclass
class Finding:
    symbol: str
    status: str           # REMOVED | ADDED | CHANGED-SIGNATURE
    breaking: bool
    reasons: list[str] = field(default_factory=list)
    old_sig: str = ""
    new_sig: str = ""

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol, "status": self.status, "breaking": self.breaking,
            "reasons": self.reasons, "old_sig": self.old_sig, "new_sig": self.new_sig,
        }


# --- surface extraction -------------------------------------------------------


def _default_repr(node) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return "<default>"


def _params(a: ast.arguments) -> list[Param]:
    out: list[Param] = []
    pos_defaults = a.defaults  # rightmost posonly+args defaults
    positional = list(a.posonlyargs) + list(a.args)
    n_no_default = len(positional) - len(pos_defaults)
    for i, arg in enumerate(positional):
        kind = POS if i < len(a.posonlyargs) else PK
        if i >= n_no_default:
            out.append(Param(kind, arg.arg, True, _default_repr(pos_defaults[i - n_no_default])))
        else:
            out.append(Param(kind, arg.arg))
    if a.vararg:
        out.append(Param(VAR, a.vararg.arg))
    for arg, dflt in zip(a.kwonlyargs, a.kw_defaults):
        out.append(Param(KW, arg.arg, dflt is not None, _default_repr(dflt) if dflt is not None else ""))
    if a.kwarg:
        out.append(Param(KWARG, a.kwarg.arg))
    return out


def _render(params: list[Param]) -> str:
    parts: list[str] = []
    seen_pos_only = False
    star_emitted = any(p.kind == VAR for p in params)
    for i, p in enumerate(params):
        if p.kind == POS:
            seen_pos_only = True
        elif seen_pos_only:
            parts.append("/")
            seen_pos_only = False
        if p.kind == KW and not star_emitted:
            parts.append("*")
            star_emitted = True
        parts.append(p.render())
    if seen_pos_only:
        parts.append("/")
    return "(" + ", ".join(parts) + ")"


def _module_all(tree: ast.Module) -> set[str] | None:
    """names in a module-level `__all__` list/tuple of string constants, or None if absent."""
    for node in tree.body:
        targets = []
        if isinstance(node, ast.Assign):
            targets = [t for t in node.targets if isinstance(t, ast.Name)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            targets = [node.target]
        if any(t.id == "__all__" for t in targets) and isinstance(node.value, (ast.List, ast.Tuple)):
            names = set()
            for el in node.value.elts:
                if isinstance(el, ast.Constant) and isinstance(el.value, str):
                    names.add(el.value)
            return names
    return None


def _class_entry(node: ast.ClassDef) -> dict:
    """public surface of a class: its public methods (plus __init__) and their signatures."""
    methods = {}
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if item.name == "__init__" or not item.name.startswith("_"):
                methods[item.name] = _params(item.args)
    return {"kind": "class", "methods": methods}


def _module_surface(path: str, modname: str, surface: dict) -> None:
    try:
        tree = ast.parse(open(path, encoding="utf-8").read())
    except (SyntaxError, UnicodeDecodeError, OSError):
        return
    allowed = _module_all(tree)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            public = name in allowed if allowed is not None else not name.startswith("_")
            if not public:
                continue
            key = f"{modname}:{name}"
            if isinstance(node, ast.ClassDef):
                surface[key] = _class_entry(node)
            else:
                surface[key] = {"kind": "function", "params": _params(node.args)}


def public_surface(root: str) -> dict[str, dict]:
    """map 'module:Symbol' -> signature entry for every public module-level function/class
    under `root` (a source tree, or a single .py file)."""
    surface: dict[str, dict] = {}
    if os.path.isfile(root):
        _module_surface(root, os.path.splitext(os.path.basename(root))[0], surface)
        return surface
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", ".git"} and not d.startswith("_")]
        for fn in sorted(files):
            if not fn.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), root)
            parts = rel[:-3].split(os.sep)
            if parts[-1] == "__init__":
                parts = parts[:-1]
            if any(p.startswith("_") for p in parts):   # private module -> not public surface
                continue
            modname = ".".join(parts) if parts else os.path.basename(os.path.normpath(root))
            _module_surface(os.path.join(dirpath, fn), modname, surface)
    return surface


# --- signature comparison -------------------------------------------------------


def _compare_params(old: list[Param], new: list[Param]) -> tuple[bool, bool, list[str]]:
    """(changed, breaking, reasons) between two parameter lists."""
    changed = old != new
    breaking = False
    reasons: list[str] = []
    old_named = {p.name: p for p in old if p.kind in (POS, PK, KW)}
    new_named = {p.name: p for p in new if p.kind in (POS, PK, KW)}
    old_positional = [p for p in old if p.kind in (POS, PK)]
    new_positional = [p for p in new if p.kind in (POS, PK)]

    # positional slots must line up: same order, and a pk name must not change
    renamed_targets: set[str] = set()
    for i, op in enumerate(old_positional):
        if i >= len(new_positional):
            if op.name in new_named and new_named[op.name].kind == KW:
                breaking = True
                reasons.append(f"param '{op.name}' became keyword-only (positional callers break)")
            elif op.name not in new_named:
                breaking = True
                reasons.append(f"param '{op.name}' removed")
            continue
        np = new_positional[i]
        if op.name != np.name:
            renamed_targets.add(np.name)
            if op.kind == POS and np.kind == POS:
                reasons.append(f"positional-only param '{op.name}' renamed to '{np.name}'")
            else:
                breaking = True
                reasons.append(f"param '{op.name}' renamed to '{np.name}' (keyword callers break)")
        elif op.kind == PK and np.kind == POS:
            breaking = True
            reasons.append(f"param '{op.name}' became positional-only (keyword callers break)")
        if op.has_default and not np.has_default and op.name == np.name:
            breaking = True
            reasons.append(f"param '{op.name}' lost its default")
        elif op.has_default and np.has_default and op.default != np.default and op.name == np.name:
            reasons.append(f"default of '{op.name}' changed: {op.default} -> {np.default}")

    # keyword-only params of the old signature must survive as keyword-passable
    for op in (p for p in old if p.kind == KW):
        np = new_named.get(op.name)
        if np is None:
            breaking = True
            reasons.append(f"keyword-only param '{op.name}' removed")
            continue
        if np.kind == POS:
            breaking = True
            reasons.append(f"param '{op.name}' became positional-only (keyword callers break)")
        if op.has_default and not np.has_default:
            breaking = True
            reasons.append(f"param '{op.name}' lost its default")
        elif op.has_default and np.has_default and op.default != np.default:
            reasons.append(f"default of '{op.name}' changed: {op.default} -> {np.default}")

    # a *args / **kwargs the old signature accepted must still be accepted
    for kind, label in ((VAR, "*args"), (KWARG, "**kwargs")):
        if any(p.kind == kind for p in old) and not any(p.kind == kind for p in new):
            breaking = True
            reasons.append(f"{label} catch-all removed")

    # new params callers never passed: fine if optional or catch-all, breaking if required
    for np in new:
        if np.name in old_named or np.name in renamed_targets or np.kind in (VAR, KWARG):
            continue
        if not np.has_default:
            breaking = True
            reasons.append(f"new required param '{np.name}'")
        else:
            reasons.append(f"new optional param '{np.name}'")
    return changed, breaking, reasons


def _sig_of(entry: dict) -> str:
    if entry["kind"] == "function":
        return _render(entry["params"])
    return "class{" + ", ".join(
        f"{m}{_render(ps)}" for m, ps in sorted(entry["methods"].items())) + "}"


def _compare_entries(sym: str, old: dict, new: dict) -> Finding | None:
    if old["kind"] != new["kind"]:
        return Finding(sym, "CHANGED-SIGNATURE", True,
                       [f"{old['kind']} became {new['kind']}"], _sig_of(old), _sig_of(new))
    if old["kind"] == "function":
        changed, breaking, reasons = _compare_params(old["params"], new["params"])
        if not changed and not reasons:
            return None
        return Finding(sym, "CHANGED-SIGNATURE", breaking, reasons,
                       _render(old["params"]), _render(new["params"]))
    # class: compare its public methods
    breaking = False
    reasons: list[str] = []
    for m, ps in old["methods"].items():
        if m not in new["methods"]:
            breaking = True
            reasons.append(f"public method '{m}' removed")
            continue
        ch, brk, rs = _compare_params(ps, new["methods"][m])
        breaking = breaking or brk
        reasons.extend(f"{m}: {r}" for r in rs)
    for m in new["methods"]:
        if m not in old["methods"]:
            reasons.append(f"new public method '{m}'")
    if not reasons:
        return None
    return Finding(sym, "CHANGED-SIGNATURE", breaking, reasons, _sig_of(old), _sig_of(new))


def diff_trees(old_root: str, new_root: str) -> tuple[list[Finding], str]:
    """Compare the public surfaces of two trees (or two files).
    Returns (findings, verdict) with verdict 'BREAKING' or 'COMPATIBLE'."""
    old_s, new_s = public_surface(old_root), public_surface(new_root)
    findings: list[Finding] = []
    for sym in sorted(old_s):
        if sym not in new_s:
            findings.append(Finding(sym, "REMOVED", True, ["public symbol removed"],
                                    _sig_of(old_s[sym]), ""))
        else:
            f = _compare_entries(sym, old_s[sym], new_s[sym])
            if f:
                findings.append(f)
    for sym in sorted(new_s):
        if sym not in old_s:
            findings.append(Finding(sym, "ADDED", False, [], "", _sig_of(new_s[sym])))
    verdict = "BREAKING" if any(f.breaking for f in findings) else "COMPATIBLE"
    return findings, verdict


# --- CLI ------------------------------------------------------------------------


def register_cli(sub) -> None:
    pa = sub.add_parser(
        "apidiff",
        help="diff the public API surface of two trees (a separate consolidation-time check)")
    pa.add_argument("old", help="the tree (or file) before the change")
    pa.add_argument("new", help="the tree (or file) after the change")
    pa.add_argument("--json", action="store_true")


def run_cli(args) -> int:
    import json as _json

    findings, verdict = diff_trees(args.old, args.new)
    if args.json:
        print(_json.dumps({"verdict": verdict,
                           "findings": [f.to_dict() for f in findings]}, indent=2))
        return 1 if verdict == "BREAKING" else 0
    if not findings:
        print("public surface identical")
    for f in findings:
        flag = "BREAKING" if f.breaking else "ok"
        print(f"  {f.status:<18} {f.symbol:<40} {flag}")
        if f.old_sig or f.new_sig:
            print(f"      old {f.old_sig or '-'}")
            print(f"      new {f.new_sig or '-'}")
        for r in f.reasons:
            print(f"      - {r}")
    n_breaking = sum(1 for f in findings if f.breaking)
    print(f"\nverdict: {verdict}"
          + (f" ({n_breaking} breaking change{'s' if n_breaking != 1 else ''})" if n_breaking else ""))
    print("note: syntactic compatibility only — behavioural evidence and human review are separate.")
    return 1 if verdict == "BREAKING" else 0

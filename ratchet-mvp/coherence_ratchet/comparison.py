"""Bounded behavioural comparison for proposed consolidations.

A counterexample refutes behavioural equivalence. Exhausting the generated or supplied cases only
reports that no divergence was found in that space. Formal verification and model checking belong to
separate evidence tiers and use separate artefacts.
"""
from __future__ import annotations

import copy
import importlib
import importlib.util
import inspect
import itertools
import json
import os
import sys

_SEEDS = {
    float: [0.0, 0.5, 0.05, 0.005, -0.5, 1.5, 2.5, 12.5, 0.125, 0.135, 1.005, 2.675, 99.995],
    int: [0, 1, 2, 3, 4, 5, -1, 10, 100],
    str: ["", "a", "abc", "  ", "café", "x" * 40],
    bool: [True, False],
    list: [[], [1], [1, 2, 3]],
    dict: [{}, {"k": "v"}],
}
_EMPTY = inspect.Parameter.empty


def _load(ref: str):
    """Import one 'root::module.func' reference.

    The two sides of a comparison are usually the same package under two roots, a before and an
    after directory. Python caches imports by module name, so loading the second side would return
    the first side's module and both references would resolve to one function object: the comparison
    then compares a function with itself and reports NO_DIVERGENCE_FOUND however far the two have
    actually diverged. That is a false clear on the rung the verification ladder leans on hardest,
    so the import runs against a saved copy of sys.modules that is restored afterwards. Each side is
    imported as if it were the first.
    """
    if "::" not in ref:
        raise ValueError(f"ref must be 'root::module.func', got {ref!r}")
    root, dotted = ref.split("::", 1)
    modname, funcname = dotted.rsplit(".", 1)
    root = os.path.abspath(root)
    saved = dict(sys.modules)
    top = modname.split(".", 1)[0]
    for name in [m for m in sys.modules if m == top or m.startswith(top + ".")
                 or m == modname or m.startswith(modname + ".")]:
        del sys.modules[name]
    sys.path.insert(0, root)
    try:
        module = importlib.import_module(modname)
        return getattr(module, funcname)
    finally:
        if sys.path and sys.path[0] == root:
            sys.path.pop(0)
        sys.modules.clear()
        sys.modules.update(saved)


def _load_strategy(path: str):
    path = os.path.abspath(path)
    directory = os.path.dirname(path)
    sys.path.insert(0, directory)
    try:
        spec = importlib.util.spec_from_file_location("_coherence_strategy", path)
        module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise ValueError(f"cannot load strategy {path}")
        spec.loader.exec_module(module)
    finally:
        if sys.path and sys.path[0] == directory:
            sys.path.pop(0)
    if not hasattr(module, "cases"):
        raise ValueError(f"strategy {path} must define cases()")
    return module.cases


def _candidates(parameter):
    if parameter.annotation in _SEEDS:
        return _SEEDS[parameter.annotation]
    if parameter.default is not _EMPTY and type(parameter.default) in _SEEDS:
        return _SEEDS[type(parameter.default)]
    return None


def _auto_cases(function, max_cases):
    try:
        signature = inspect.signature(function)
    except (ValueError, TypeError):
        return None
    per_parameter = []
    for parameter in signature.parameters.values():
        if parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
            continue
        values = _candidates(parameter)
        if values is None:
            if parameter.default is not _EMPTY:
                per_parameter.append([parameter.default])
                continue
            return None
        per_parameter.append(values)
    if not per_parameter:
        return [((), {})]
    return [
        (tuple(combo), {})
        for combo in itertools.islice(itertools.product(*per_parameter), max_cases)
    ]


def _observe(function, args, kwargs):
    try:
        return ("return", function(*args, **kwargs))
    except Exception as exc:
        return ("raise", type(exc).__name__)


def _equal(left, right):
    try:
        return bool(left == right)
    except Exception:
        return repr(left) == repr(right)


def _observations_equal(left, right):
    if left[0] != right[0]:
        return False
    return _equal(left[1], right[1]) if left[0] == "return" else left[1] == right[1]


def _show(observation):
    return f"returns {observation[1]!r}" if observation[0] == "return" else f"raises {observation[1]}"


def _unproven(original_ref, replacement_ref, reason):
    return {
        "verdict": "UNPROVEN",
        "reason": reason,
        "original": original_ref,
        "replacement": replacement_ref,
        "cases_run": 0,
        "input_source": None,
        "counterexamples": [],
        "note": "comparison could not establish a supported deterministic case set",
    }


def compare(original_ref, replacement_ref, *, max_cases=500, strategy=None,
            max_counterexamples=5):
    """Compare a replacement with the original over a bounded set of deterministic cases."""
    try:
        original = _load(original_ref)
        replacement = _load(replacement_ref)
        if strategy:
            raw_cases = list(_load_strategy(strategy)())
            input_source = "strategy"
        else:
            raw_cases = _auto_cases(replacement, max_cases) or _auto_cases(original, max_cases)
            input_source = "auto-generated seeds"
    except (AttributeError, ImportError, OSError, TypeError, ValueError) as exc:
        return _unproven(original_ref, replacement_ref, f"unable to prepare comparison: {exc}")

    if raw_cases is None:
        return _unproven(
            original_ref, replacement_ref,
            "signature has a required parameter of unknown type; supply --strategy",
        )

    counterexamples = []
    cases_run = 0
    for case in raw_cases:
        if callable(case):
            original_args, original_kwargs = case()
            replacement_args, replacement_kwargs = case()
            shown = "<strategy case>"
        else:
            original_args, original_kwargs = case
            shown = f"args={original_args!r}" + (
                f" kwargs={original_kwargs!r}" if original_kwargs else ""
            )
            # Each side gets its own copy. The seed corpus carries lists and dicts, and binding one
            # object to both sides let the first implementation mutate the input the second was
            # about to receive: two byte-identical functions that append to their argument were
            # reported REFUTED, the original returning 1 and the replacement 2. A counterexample
            # that only says the original ran first is not a behavioural difference.
            replacement_args = copy.deepcopy(original_args)
            replacement_kwargs = copy.deepcopy(original_kwargs)
        cases_run += 1
        original_observation = _observe(original, original_args, original_kwargs)
        replacement_observation = _observe(replacement, replacement_args, replacement_kwargs)
        if not _observations_equal(original_observation, replacement_observation):
            counterexamples.append({
                "input": shown,
                "original": _show(original_observation),
                "replacement": _show(replacement_observation),
            })
            if len(counterexamples) >= max_counterexamples:
                break

    refuted = bool(counterexamples)
    return {
        "verdict": "REFUTED" if refuted else "NO_DIVERGENCE_FOUND",
        "original": original_ref,
        "replacement": replacement_ref,
        "cases_run": cases_run,
        "input_source": input_source,
        "counterexamples": counterexamples,
        "note": (
            "behavioural divergence found; the replacement is not equivalent"
            if refuted else
            "no divergence found in the tested space; this is not a formal proof and does not "
            "cover side effects or non-determinism"
        ),
    }


def to_markdown(packet: dict) -> str:
    lines = [
        "# Bounded behavioural comparison",
        "",
        f"- **Verdict:** {packet['verdict']}",
        f"- **Original:** `{packet['original']}`",
        f"- **Replacement:** `{packet['replacement']}`",
        f"- **Cases run:** {packet['cases_run']} ({packet.get('input_source')})",
        f"- {packet['note']}",
    ]
    if packet["counterexamples"]:
        lines += ["", "## Counterexamples", ""]
        for counterexample in packet["counterexamples"]:
            lines.append(
                f"- `{counterexample['input']}`: original {counterexample['original']}; "
                f"replacement {counterexample['replacement']}"
            )
    return "\n".join(lines) + "\n"


def render(packet: dict) -> None:
    mark = {"NO_DIVERGENCE_FOUND": "✓", "REFUTED": "✗", "UNPROVEN": "?"}[packet["verdict"]]
    print(f"  {mark} {packet['verdict']} — {packet['cases_run']} cases ({packet.get('input_source')})")
    print(f"    original: {packet['original']}")
    print(f"    replacement: {packet['replacement']}")
    if packet.get("reason"):
        print(f"    {packet['reason']}")
    for counterexample in packet["counterexamples"]:
        print(
            f"    ✗ {counterexample['input']}: original {counterexample['original']} "
            f"≠ replacement {counterexample['replacement']}"
        )
    print(f"    {packet['note']}")


def register_cli(sub) -> None:
    parser = sub.add_parser("compare", help="bounded behavioural comparison of a consolidation")
    parser.add_argument("original", help="original implementation as 'root::module.func'")
    parser.add_argument("replacement", help="replacement implementation as 'root::module.func'")
    parser.add_argument("--cases", type=int, default=500, help="maximum auto-generated cases")
    parser.add_argument("--strategy", help="Python file exporting cases() for custom inputs")
    parser.add_argument("--out", help="write the comparison packet as Markdown")
    parser.add_argument("--json", action="store_true")


def run_cli(args) -> int:
    packet = compare(args.original, args.replacement, max_cases=args.cases, strategy=args.strategy)
    if args.json:
        print(json.dumps(packet, indent=2, sort_keys=True, default=repr))
    else:
        render(packet)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as stream:
            stream.write(to_markdown(packet))
        if not args.json:
            print(f"    comparison packet written to {args.out}")
    return {"NO_DIVERGENCE_FOUND": 0, "REFUTED": 1, "UNPROVEN": 2}[packet["verdict"]]


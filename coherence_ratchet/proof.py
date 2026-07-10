"""The behaviour-complete proof — the third layer, the brake on consolidation.

The experiments (`autonomous-consolidation.md`, `integrator-agent.md`) proved this layer is
non-negotiable: existing characterisation suites are *porous*, so a consolidation can pass every test
while silently changing behaviour — a 4→3 retry-count, retrying a `ValueError` that should propagate,
a `price_to_cents` rounding flip from HALF_UP to HALF_EVEN. In those experiments the only thing that
caught such changes was a human reading carefully; nothing in the harness did. This module IS that
missing harness.

It does one thing: given the ORIGINAL implementation and the CANONICAL replacement a consolidation
proposes, run both over the same inputs — including an **adversarial seed library aimed at the change
points a porous suite misses** — and compare observed behaviour (return value AND raised-exception
type). If they ever differ, the consolidation is REFUTED with a counterexample; otherwise it is PROVED
up to the tested space.

Honest framing, baked in: this is property-based *differential* testing. It is decisive at refutation
(a counterexample is proof of a behaviour change); "PROVED" means no counterexample was found in the
tested space, not a formal equivalence proof. Side effects, I/O, time, and randomness are out of the
deterministic core — those the steward reviews in the behavioural diff. Deterministic, offline, no LLM:
the integrator/agent is the engine, this is the brake.
"""
from __future__ import annotations

import importlib
import importlib.util
import inspect
import itertools
import json
import os
import sys

# Adversarial seeds per type — aimed at the change points a porous characterisation suite waves
# through. Half-boundary floats expose rounding-mode flips (HALF_UP vs HALF_EVEN); small integers
# expose off-by-one counts; empty/singleton collections and the exception set expose selectivity.
_SEEDS = {
    float: [0.0, 0.5, 0.05, 0.005, -0.5, 1.5, 2.5, 12.5, 0.125, 0.135, 1.005, 2.675, 99.995],
    int: [0, 1, 2, 3, 4, 5, -1, 10, 100],
    str: ["", "a", "abc", "  ", "café", "x" * 40],
    bool: [True, False],
    list: [[], [1], [1, 2, 3]],
    dict: [{}, {"k": "v"}],
}

_EMPTY = inspect.Parameter.empty


# --- loading the two implementations ----------------------------------------

def _load(ref: str):
    """Load a callable from 'root::module.func' via normal import (cached in sys.modules), so the
    original, the canonical, and the strategy share ONE module instance — meaning exception classes
    have a single identity and `except SomeError` behaves correctly.

    Recommended workflow: keep both implementations importable in one tree during review (e.g. copy
    the original to `to_cents_legacy` and prove it against the new canonical). LIMITATION: two
    different trees that share a module name collide in sys.modules (first import wins); for that
    pre/post-tree case, load them under distinct module names or run the proof in separate processes.
    Behaviour is compared by exception *name*, so cross-tree class identity is not required — only
    same-run intra-module `except` semantics are, which the shared instance gives."""
    if "::" not in ref:
        raise ValueError(f"ref must be 'root::module.func', got {ref!r}")
    root, dotted = ref.split("::", 1)
    modname, funcname = dotted.rsplit(".", 1)
    root = os.path.abspath(root)
    sys.path.insert(0, root)
    try:
        mod = importlib.import_module(modname)
        return getattr(mod, funcname)
    finally:
        if sys.path and sys.path[0] == root:
            sys.path.pop(0)


def _load_strategy(path: str):
    """Load a strategy module exporting cases() — the escape hatch for signatures auto-generation
    can't build (higher-order functions, custom objects). cases() yields (args, kwargs) for immutable
    inputs, or zero-arg thunks returning (args, kwargs) when the input carries mutable state."""
    path = os.path.abspath(path)
    d = os.path.dirname(path)
    sys.path.insert(0, d)
    try:
        spec = importlib.util.spec_from_file_location("_coherence_strategy", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        if sys.path and sys.path[0] == d:
            sys.path.pop(0)
    if not hasattr(mod, "cases"):
        raise ValueError(f"strategy {path} must define cases()")
    return mod.cases


# --- input generation -------------------------------------------------------

def _candidates(param):
    """Seed values for one parameter, by annotation then by default's type; None if unknown."""
    ann = param.annotation
    if ann in _SEEDS:
        return _SEEDS[ann]
    if param.default is not _EMPTY and type(param.default) in _SEEDS:
        return _SEEDS[type(param.default)]
    return None


def _auto_cases(fn, max_cases):
    """Cartesian product of per-parameter seeds, capped. Returns None if a required parameter's type
    can't be inferred (then a --strategy is required)."""
    try:
        sig = inspect.signature(fn)
    except (ValueError, TypeError):
        return None
    per = []
    for p in sig.parameters.values():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        c = _candidates(p)
        if c is None:
            if p.default is not _EMPTY:
                per.append([p.default])       # optional unknown: hold at its default
                continue
            return None                       # required + unknown -> cannot auto-generate
        per.append(c)
    if not per:
        return [((), {})]
    return [(tuple(combo), {}) for combo in itertools.islice(itertools.product(*per), max_cases)]


# --- observing and comparing behaviour --------------------------------------

def _observe(fn, args, kwargs):
    """Observed behaviour = ('return', value) or ('raise', ExceptionTypeName)."""
    try:
        return ("return", fn(*args, **kwargs))
    except Exception as exc:  # the exception TYPE is part of observable behaviour (selectivity)
        return ("raise", type(exc).__name__)


def _equal(a, b):
    try:
        return bool(a == b)
    except Exception:
        return repr(a) == repr(b)


def _obs_equal(o1, o2):
    if o1[0] != o2[0]:
        return False
    return _equal(o1[1], o2[1]) if o1[0] == "return" else o1[1] == o2[1]


def _show(obs):
    return f"returns {obs[1]!r}" if obs[0] == "return" else f"raises {obs[1]}"


# --- the proof ---------------------------------------------------------------

def prove(original_ref, canonical_ref, *, max_cases=500, strategy=None, max_counterexamples=5):
    """Differentially test canonical against original. Returns a PROOF packet dict."""
    fn_orig = _load(original_ref)
    fn_canon = _load(canonical_ref)

    if strategy:
        raw = list(_load_strategy(strategy)())
        source = "strategy"
    else:
        raw = _auto_cases(fn_canon, max_cases) or _auto_cases(fn_orig, max_cases)
        source = "auto-generated seeds"
        if raw is None:
            return {
                "verdict": "UNPROVEN",
                "reason": "signature has a required parameter of unknown type — supply --strategy",
                "original": original_ref, "canonical": canonical_ref,
                "cases_run": 0, "input_source": None, "counterexamples": [],
            }

    counterexamples = []
    run = 0
    for case in raw:
        # A thunk yields fresh inputs per implementation (needed when an input carries mutable state,
        # e.g. an operation that fails k times); a plain (args, kwargs) is shared (immutable inputs).
        if callable(case):
            args_o, kw_o = case()
            args_c, kw_c = case()
            shown = "<strategy case>"
        else:
            args_o, kw_o = case
            args_c, kw_c = case
            shown = f"args={args_o!r}" + (f" kwargs={kw_o!r}" if kw_o else "")
        run += 1
        obs_o = _observe(fn_orig, args_o, kw_o)
        obs_c = _observe(fn_canon, args_c, kw_c)
        if not _obs_equal(obs_o, obs_c):
            counterexamples.append({
                "input": shown,
                "original": _show(obs_o),
                "canonical": _show(obs_c),
            })
            if len(counterexamples) >= max_counterexamples:
                break

    return {
        "verdict": "REFUTED" if counterexamples else "PROVED",
        "original": original_ref,
        "canonical": canonical_ref,
        "cases_run": run,
        "input_source": source,
        "counterexamples": counterexamples,
        "note": ("behaviour change found — consolidation is NOT behaviour-preserving"
                 if counterexamples else
                 "no counterexample in the tested space (not a formal proof; side effects/"
                 "non-determinism not covered — steward reviews the diff)"),
    }


# --- artefact + rendering ----------------------------------------------------

def to_markdown(packet: dict) -> str:
    lines = [
        "# PROOF — behaviour-complete consolidation proof",
        "",
        f"- **Verdict:** {packet['verdict']}",
        f"- **Original:** `{packet['original']}`",
        f"- **Canonical:** `{packet['canonical']}`",
        f"- **Cases run:** {packet['cases_run']} ({packet.get('input_source')})",
        f"- {packet['note']}",
    ]
    if packet["counterexamples"]:
        lines += ["", "## Counterexamples (behaviour changed here)", ""]
        for c in packet["counterexamples"]:
            lines.append(f"- `{c['input']}` — original {c['original']}, canonical {c['canonical']}")
    return "\n".join(lines) + "\n"


def render(packet: dict) -> None:
    mark = {"PROVED": "✓", "REFUTED": "✗", "UNPROVEN": "?"}.get(packet["verdict"], "?")
    print(f"  {mark} {packet['verdict']} — {packet['cases_run']} cases ({packet.get('input_source')})")
    print(f"    original:  {packet['original']}")
    print(f"    canonical: {packet['canonical']}")
    if packet.get("reason"):
        print(f"    {packet['reason']}")
    for c in packet["counterexamples"]:
        print(f"    ✗ {c['input']}: original {c['original']} ≠ canonical {c['canonical']}")
    print(f"    {packet['note']}")


# --- CLI wiring (called from cli.py) ----------------------------------------

def register_cli(sub) -> None:
    p = sub.add_parser("prove", help="behaviour-complete proof: differentially test a proposed consolidation")
    p.add_argument("original", help="original impl as 'root::module.func'")
    p.add_argument("canonical", help="canonical replacement as 'root::module.func'")
    p.add_argument("--cases", type=int, default=500, help="max auto-generated cases")
    p.add_argument("--strategy", help="strategy .py exporting cases() for signatures auto-gen can't build")
    p.add_argument("--out", help="write the PROOF packet as markdown to this path")
    p.add_argument("--json", action="store_true")


def run_cli(args) -> int:
    packet = prove(args.original, args.canonical, max_cases=args.cases, strategy=args.strategy)
    if args.json:
        print(json.dumps(packet, indent=2, sort_keys=True, default=repr))
    else:
        render(packet)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(to_markdown(packet))
        if not args.json:
            print(f"    proof packet written to {args.out}")
    return 1 if packet["verdict"] != "PROVED" else 0

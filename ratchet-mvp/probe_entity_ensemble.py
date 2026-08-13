"""Probe N3 — how often do independent agents agree on an entity's shape?

`entity-coherence.md` recorded five independent agents producing five mutually incompatible order
schemas where a single agent produced one. That is an existence result at the level that matters: one
ensemble, n=1. The claim the book makes from it is distributional, so the measurement should be too.

Each trial is one agent working alone on the same task, with no sight of any other agent's output.
Trials are grouped into ensembles of five after the fact, which is equivalent to running ensembles
directly because the agents are independent by construction, and it lets one dispatch produce twenty
ensembles instead of one.

Two arms:

    independent   the task alone. Nothing tells an agent what an order looks like here.
    grounded      the same task, plus a ratified entity shape naming the canonical field set.

The scorer reads the string keys each produced module uses for the order mapping, canonicalises them
into a frozen set, and counts how many distinct sets an ensemble contains. One distinct shape means
five agents agreed. Five means they produced five incompatible representations, which is the case the
original run found once.
"""

from __future__ import annotations

import ast
import os
import sys

ENSEMBLE_SIZE = 5

CONDITIONS = ("independent", "grounded")

_TASK = (
    "Write a module `orders/build.py` containing `def build_order(customer_id, items)` which returns "
    "a dictionary representing a customer order. `items` is a list of dictionaries each carrying a "
    "product id, a quantity and a unit price in cents. The returned order must carry the customer, "
    "the line items, and the order total. Use only the Python standard library and no network "
    "calls: this is a pure function over its arguments. Return ONLY the full source of "
    "orders/build.py in one Python code block, no prose."
)

_RATIFIED = (
    "This system's ratified Order contract, approved by the orders architecture owner, defines the "
    "canonical field set. Use exactly these keys and no others at the top level:\n"
    "  order_id, customer_id, lines, total_cents, currency, created_at\n"
    "Each entry in `lines` uses exactly: product_id, quantity, unit_price_cents\n"
)


def build_prompt(condition: str) -> str:
    if condition == "independent":
        return _TASK
    if condition == "grounded":
        return _RATIFIED + "\n" + _TASK
    raise ValueError(condition)


# --- deterministic scorer ---------------------------------------------------

def _keys_of(node) -> set[str]:
    """String keys an expression contributes to a mapping: a literal, a dict() call, or an unpacking."""
    out: set[str] = set()
    if isinstance(node, ast.Dict):
        for k in node.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                out.add(k.value)
            elif k is None:  # {**other}
                pass
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
        out |= {kw.arg for kw in node.keywords if kw.arg}
    return out


def _order_keys(code: str) -> frozenset[str]:
    """The keys of the order `build_order` returns, and only those.

    An earlier version collected every string key in the module, which counted incidental dicts as
    part of the entity's shape. Some trials build an unrelated mapping on the way past, and one model
    reached for an HTTP client and produced request envelopes, so the module's dict vocabulary is a
    much wider thing than the order's field set. Reading the returned mapping keeps the measurement on
    the quantity the experiment is about.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return frozenset()

    fn = next((n for n in ast.walk(tree)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "build_order"),
              None)
    if fn is None:
        return frozenset()

    returned_names: set[str] = set()
    keys: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Return) and node.value is not None:
            if isinstance(node.value, ast.Name):
                returned_names.add(node.value.id)
            else:
                keys |= _keys_of(node.value)

    # An order assembled by assignment: order["total_cents"] = ... then returned.
    if returned_names:
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if (isinstance(tgt, ast.Subscript) and isinstance(tgt.value, ast.Name)
                            and tgt.value.id in returned_names
                            and isinstance(tgt.slice, ast.Constant)
                            and isinstance(tgt.slice.value, str)):
                        keys.add(tgt.slice.value)
            # The order bound to the returned name, however it was assembled: a literal, a dict()
            # call with keyword arguments, or an unpacking of another mapping.
            if isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if not (isinstance(tgt, ast.Name) and tgt.id in returned_names):
                        continue
                    keys |= _keys_of(node.value)
            # order.update({...}) on the returned name
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "update"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in returned_names):
                for arg in node.args:
                    keys |= _keys_of(arg)
    return frozenset(keys)


def score_code(code: str, *_names) -> dict:
    keys = _order_keys(code)
    return {"keys": sorted(keys), "n_keys": len(keys), "shape": "|".join(sorted(keys))}


def _ensembles(rows: list[dict], size: int = ENSEMBLE_SIZE) -> list[list[dict]]:
    return [rows[i:i + size] for i in range(0, len(rows) - size + 1, size)]


def tally(results_dir: str) -> None:
    print(f"{'arm':<14}{'ensembles':>10}{'mean distinct':>15}{'all-agree':>11}{'all-differ':>12}")
    for cond in CONDITIONS:
        d = os.path.join(results_dir, cond)
        if not os.path.isdir(d):
            continue
        rows = []
        for name in sorted(os.listdir(d)):
            if name.endswith(".extracted.py"):
                with open(os.path.join(d, name), encoding="utf-8") as f:
                    rows.append(score_code(f.read()))
        rows = [r for r in rows if r["n_keys"]]
        groups = _ensembles(rows)
        if not groups:
            continue
        distinct = [len({r["shape"] for r in g}) for g in groups]
        print(f"{cond:<14}{len(groups):>10}{sum(distinct) / len(distinct):>15.2f}"
              f"{sum(1 for d_ in distinct if d_ == 1):>11}"
              f"{sum(1 for d_ in distinct if d_ == ENSEMBLE_SIZE):>12}")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--print":
        print(build_prompt(sys.argv[2]))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--tally":
        tally(sys.argv[2])
    else:
        print(__doc__)

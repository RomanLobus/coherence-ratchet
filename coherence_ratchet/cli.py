"""Command line for the coherence ratchet.

    coherence-ratchet measure  <path> [--repo DIR] [--json]
    coherence-ratchet init     <path> [--repo DIR] [--budgets FILE]
    coherence-ratchet check    <path> [--repo DIR] [--budgets FILE] [--tighten]
                               [--accept --owner NAME --trigger TEXT [--note TEXT] [--ledger FILE]]

`check` exits non-zero when a watched signal has worsened past its ceiling — the same contract as a
coverage ratchet failing CI. `--accept` turns a trip into an owned, dated coherence-debt ledger entry
instead of a failure (exit 0), so accepting decay is a deliberate, recorded act.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys

from .ratchet import Budget, append_ledger, check, init_budget, tighten
from .signals import measure_all

DEFAULT_BUDGETS = "coherence/budgets.json"
DEFAULT_LEDGER = "coherence/coherence-ledger.jsonl"


def _print_snapshot(snap) -> None:
    d = snap.to_dict()
    print("  duplication (function-level)")
    print(f"    functions ............ {d['total_functions']}")
    print(f"    redundant clusters ... {d['redundant_clusters']}")
    print(f"    redundant functions .. {d['redundant_functions']}")
    print(f"    duplication ratio .... {d['duplication_ratio']}")
    if "cycle_ratio" in d:
        print("  architecture")
        print(f"    modules .............. {d['n_modules']}")
        print(f"    cycle ratio .......... {d['cycle_ratio']}  (ratcheted)")
        print(f"    coupling density ..... {d['coupling_density']}  (diagnostic)")
        print(f"    max fan-in ratio ..... {d['max_fan_in_ratio']}  (diagnostic)")
        print("  connascence")
        print(f"    shared literals ...... {d['connascence_shared']}  (ratcheted)")
        if d.get("hyperliminal_pairs"):
            print("  change history")
            print(f"    hyperliminal pairs ... {d['hyperliminal_pairs']}  (diagnostic)")
            print(f"    contagion (mean) ..... {d['contagion_mean']}  (diagnostic)")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="coherence-ratchet")
    sub = p.add_subparsers(dest="cmd", required=True)

    pm = sub.add_parser("measure", help="measure a tree and print the signal portfolio")
    pm.add_argument("path")
    pm.add_argument("--repo", help="git repo for hyperliminal/contagion signals")
    pm.add_argument("--json", action="store_true")

    pi = sub.add_parser("init", help="write the baseline budget from the portfolio")
    pi.add_argument("path")
    pi.add_argument("--repo")
    pi.add_argument("--budgets", default=DEFAULT_BUDGETS)

    pc = sub.add_parser("check", help="fail if coherence worsened past the budget")
    pc.add_argument("path")
    pc.add_argument("--repo")
    pc.add_argument("--budgets", default=DEFAULT_BUDGETS)
    pc.add_argument("--tighten", action="store_true", help="ratchet ceilings down on improvement")
    pc.add_argument("--accept", action="store_true", help="record the breach as owned coherence debt instead of failing")
    pc.add_argument("--owner", help="owner of the accepted debt (required with --accept)")
    pc.add_argument("--trigger", help="dated/condition repayment trigger (required with --accept)")
    pc.add_argument("--region", default="", help="region label for the ledger entry")
    pc.add_argument("--note", default="", help="free-text note for the ledger entry")
    pc.add_argument("--ledger", default=DEFAULT_LEDGER)

    # selfmodel subcommands are registered by Move 1 (selfmodel.py); wired here if present.
    try:
        from . import selfmodel as _sm

        _sm.register_cli(sub)
    except Exception:
        pass

    # gate: the optional LLM semantic layer over the deterministic residue.
    try:
        from . import gate as _gate

        _gate.register_cli(sub)
    except Exception:
        pass

    # prove: the behaviour-complete proof (the third layer, the brake on consolidation).
    try:
        from . import proof as _proof

        _proof.register_cli(sub)
    except Exception:
        pass

    # report: leading-indicator report over the coherence-debt ledger.
    try:
        from . import report as _report

        _report.register_cli(sub)
    except Exception:
        pass

    args = p.parse_args(argv)

    if args.cmd == "measure":
        snap = measure_all(args.path, repo=getattr(args, "repo", None))
        if args.json:
            print(json.dumps(snap.to_dict(), indent=2, sort_keys=True))
        else:
            _print_snapshot(snap)
        return 0

    if args.cmd == "init":
        budget = init_budget(args.path, args.budgets, repo=getattr(args, "repo", None))
        print(f"baseline budget written to {args.budgets}")
        for m, v in sorted(budget.ceilings.items()):
            print(f"  {m} <= {v}")
        return 0

    if args.cmd == "check":
        snap, breaches, improvements = check(args.path, args.budgets, repo=getattr(args, "repo", None))
        _print_snapshot(snap)
        if breaches:
            print("\nRATCHET TRIPPED — coherence worsened past budget:")
            for b in breaches:
                print(f"  ✗ {b.metric}: {b.observed} > ceiling {b.ceiling} (+{b.delta})")
            if args.accept:
                if not (args.owner and args.trigger):
                    print("\n--accept requires --owner and --trigger.", file=sys.stderr)
                    return 2
                append_ledger(
                    args.ledger,
                    when=datetime.date.today().isoformat(),
                    region=args.region or args.path,
                    breaches=breaches,
                    owner=args.owner,
                    repayment_trigger=args.trigger,
                    note=args.note,
                )
                print(f"\nAccepted as coherence debt → {args.ledger}")
                print(f"  owner: {args.owner}   repayment trigger: {args.trigger}")
                return 0
            print("\nReuse the existing pattern, or accept the debt: --accept --owner NAME --trigger TEXT")
            return 1
        if improvements:
            print("\nCoherence improved:")
            for m, (old, new) in sorted(improvements.items()):
                print(f"  ✓ {m}: {old} -> {new}")
            if args.tighten:
                tighten(Budget.load(args.budgets), snap).save(args.budgets)
                print("ratchet tightened: ceilings lowered to the new floor.")
        print("\nOK — coherence held.")
        return 0

    if args.cmd and args.cmd.startswith("selfmodel"):
        from . import selfmodel as _sm

        return _sm.run_cli(args)

    if args.cmd == "gate":
        from . import gate as _gate

        return _gate.run_cli(args)

    if args.cmd == "prove":
        from . import proof as _proof

        return _proof.run_cli(args)

    if args.cmd == "report":
        from . import report as _report

        return _report.run_cli(args)

    return 2


if __name__ == "__main__":
    sys.exit(main())
